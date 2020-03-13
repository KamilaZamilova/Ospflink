#!/usr/bin/python
##
##     Copyright (C) 2018 
##     Venaimin Konoplev  <v.konoplev@cosmos.ru>
##     Space Research Institute (IKI)
##     Russia, Moscow
##
##     This program is free software; you can redistribute it and/or
##     modify it under the terms of the GNU General Public License as
##     published by the Free Software Foundation; either version 2 of the
##     License, or (at your option) any later version.

##     This program is distributed in the hope that it will be useful,
##     but WITHOUT ANY WARRANTY; without even the implied warranty of
##     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##     General Public License for more details.

##     You should have received a copy of the GNU General Public License
##     along with this program; if not, write to the Free Software
##     Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
##     02111-1307 USA

import struct, sys, argparse, string, os, os.path, time, traceback, random, re

from pysnmp.hlapi import *
from ospflink.mutils import *
from ospflink.global_var import *
from ospflink.mysyslog import *
from ospflink.dictionaries import *
from ospflink.debug_print import *
from ospflink.ospf import *
from ospflink.config_parse import * 
from ospflink.zabbix import *
from ospflink.linkdb import *

def lockfile (fh) :
    if platform.system() == "Windows" :
        start = time.time()
        sleep_time = 0.05
        while True :
            try :
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except IOError as error:
                now = time.time()
                #delay = now - start
                if now - start > LOCK_TIMEOUT :
                    print >> sys.stderr, "can not lock the file!"
                    exit(1)

                sleep_time = sleep_time*(1+random.random())
                if now + sleep_time - start > LOCK_TIMEOUT :
                    sleep_time = start + LOCK_TIMEOUT + 0.1 - now
                # print "==> %0.2f, %0.2f" % (sleep_time, now-start)
                time.sleep(sleep_time)
            else :
                break
    else :
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX) 


import platform
if platform.system() == "Windows" :
    import msvcrt
    
else :
    import fcntl
#-------------------------------------------------------------------------------

VERSION         = "1.1.RC1 (26.09.2019)" 

LSDB_REFRESH_TIME = 150
LOCK_TIMEOUT = 20
debug_filename = None

global VERBOSE

parser = argparse.ArgumentParser(description='Check OSPF link in lsadb')
parser.add_argument('--verbose', '-v', action='count', help="Be verbose")
#parser.add_argument('link_addr', help="link address to check")
parser.add_argument('param', help="link address to check or discovery mode")
args = parser.parse_args()

VERBOSE   = args.verbose
if VERBOSE > 0: Debug_Print(debug_filename)

mode = 'check_link'
link_addr = args.param

if (args.param == 'discovery'):
    mode = args.param
    link_addr = None

ospf = Ospf()
old_dict = {}
new_dict = {}
string_list = []
mask        = 0
My_Logger = []

LSDB_REFRESH_TIME, LOCK_TIMEOUT, mask, domains, syslog_platform, sp, syslog_filename, debug_filename, zabbix_filename = Config_parse(mode, link_addr, mask) 

if (len(domains) == 0) :
    print >> sys.stderr, "domain did not matched in the cofig file"
    exit(1)


if syslog_platform != None:
    if syslog_platform == 'win':
        My_Logger.append(Win_Logger(sp))

    else:
        My_Logger.append(Lin_Logger(sp))

if syslog_filename != None:
    My_Logger.append(File_Logger(syslog_filename))

lock_file = data_dir + '/common.lock'
lck = open(lock_file, "a")
lockfile(lck)

#################################################
#################################################
#################################################
for domain, agent_comm in domains.items() :

    dbfile = data_dir + '/' + domain + ".dat"

    mtime = 0
    size = 0
    dbf = None

    if not os.path.exists(dbfile) :
        open(dbfile,"a").close()

    dbf = open(dbfile, "r+")
    Creating_Old_Dict( old_dict, dbf )
    mtime = os.stat(dbfile).st_mtime  #LAST TIME UPDATED FILE
    size  = os.stat(dbfile).st_size   #size of file in bytes

    linkdb = LinkDB(dbf)

    if abs(mtime - time.time()) > LSDB_REFRESH_TIME or size == 0:  
        oid_area_prefix = "1.3.6.1.2.1.14.4.1.1"; 
        oid_lsa_prefix = "1.3.6.1.2.1.14.4.1.8"; 
        seen_areas = {}
        for agent in agent_comm['agents'].split(",") :
            try :
                addr,port = agent.split(":")       
            except ValueError :
                addr = agent
                port = 161   
            g = bulkCmd(SnmpEngine(),
                    CommunityData(agent_comm['community']),
                    UdpTransportTarget((addr, port)),
                    ContextData(),
                    0, 25,
                    ObjectType(ObjectIdentity(oid_area_prefix)),
                    ObjectType(ObjectIdentity(oid_lsa_prefix)),
                )
        
            last_area = None
            while True :
                (e, es, ei, var) = next(g) 
                if e :
                    print >> sys.stderr, "Error quering agent", agent
                    print >> sys.stderr, e
                    #exit(1)
            
                oid = var[0][0]
                if not str(oid).startswith(oid_area_prefix) : break
            
                area = var[0][1].prettyPrint()
                #
                # Prevent areas to read twice
                # from different SNMP agents
                #
                if area != last_area :
                    if area in seen_areas :
                        Debug_Print( debug_filename,"skip Area",area )
                        continue
                    linkdb.commitArea(last_area,new_dict,dbf)
                    seen_areas[area]=1
                    last_area = None
                ## lsa
                val = var[1][1]
                last_area = area
                linkdb.addLSA(ospf.parseMsg(str(val), VERBOSE, 0)[1])

            linkdb.commitArea(last_area,new_dict,dbf)

            What_to_Write(old_dict, new_dict, string_list )
            if (My_Logger):
                for logger in My_Logger:
                    for s in string_list:
                        logger.Log_Write(s)
    linkdb.load()
    

    if(mode == 'check_link'):
        (status, link, mode) = linkdb.checkLink(link_addr)
        descr = "("+",".join([domain, link, mode]) + ")"
        if status : 
            print ("UP")
        else :
            print ("DOWN")
    elif(mode == 'discovery'):
        Cash_Check (dbf, zabbix_filename,domain)

if(mode == 'discovery'):
    Json_Fill(zabbix_filename)
