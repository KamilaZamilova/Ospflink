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

from ospflink.mutils import *
from ospflink.global_var import *
from ospflink.ospf import LSA_TYPES, RTR_LINK_TYPE
from ospflink.mysyslog import *
from ospflink.dictionaries import *
from ospflink.debug_print import *
from pysnmp.hlapi import *
from ospflink.ospf import *
from ospflink.config_parse import * 
from ospflink.zabbix import *

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

class LinkDB:
    
    linkdb = {}
    netlsa = {}
    rtrlsa = {}

    dbf = None
    def __init__(self, dbf):
        self.dbf = dbf
        dbf.seek(0)
        self.linkdb.clear()
        self.netlsa.clear()
        self.rtrlsa.clear()
    #
    # TYPE := {P2P,STUB,TRANSIT,NETWORK}
    #
    
    def addLink (self, ip, mask, type) :
        if type in ("NETWORK","STUB") :
            if (ip,mask) in self.linkdb :
                t = self.linkdb[ip,mask][0]
                if t in ("NETWORK","STUB") :
                    if t == "STUB" and type == "STUB" :
                        pass
                    else :
                        self.linkdb[ip,mask] = ["NETWORK","BROKEN"]
            elif type == "STUB" :
                if mask == 0xFFFFFFFF :
                    self.linkdb[ip,mask] = ["STUB","LINKED"]
                else :
                    self.linkdb[ip,mask] = ["STUB","STUB"]
            else :
                self.linkdb[ip,mask] = ["NETWORK","LINKED"]
        else :
            self.linkdb[ip,mask] = [type,"LINKED"]
    
    def addLSA (self, lsa) :
        type = ""
        ip = ""
        mask = ""
    
        rtr = lsa["H"]["ADVRTR"]
        type  = lsa["H"]["T"]
        lsid  = lsa["H"]["LSID"]
        Debug_Print(debug_filename, rtr, 'fdkd', type, lsid)
        #print lsa
        if type == LSA_TYPES["ROUTER"] :
            if not (rtr in self.rtrlsa) :
                self.rtrlsa[rtr] = {}
            
            self.rtrlsa[rtr]["P2P"] = []
            self.rtrlsa[rtr]["STUB"] = []
            self.rtrlsa[rtr]["TRANSIT"] = []

            for (link_num,link) in lsa['V']['LINKS'].items() :
                type = RTR_LINK_TYPE[link["T"]]
                if type == "VIRTUAL" : 
                    continue
                if type == "P2P" :
                    ip = link["DATA"]
                    mask = 0xFFFFFFFF
                elif type == "STUB" :
                    mask = link["DATA"]
                    #if mask == 0xFFFFFFFF :
                    #    continue
                    ip = link["ID"]
                elif type == "TRANSIT" :
                    ip = link["DATA"]
                    mask = link["ID"]
                else :
                    raise Exception("unknown LSA router link type")
                
                if not (type in self.rtrlsa[rtr]) :
                    self.rtrlsa[rtr][type] = []
                
                self.rtrlsa[rtr][type].append([ip,mask])

        elif type == LSA_TYPES["NETWORK"] :
            mask = lsa["V"]["MASK"]
            ip = lsid & mask
            
            if not (rtr in self.netlsa) :
                self.netlsa[rtr] = []
            
            self.netlsa[rtr].append([ip, mask])
            #print( type, ip, mask)
            #linkdb.addLSA(rtr, ip, mask, type);
            #Debug_Print(debug_filename, dbf, type, id2str(ip), id2str(mask))

    def commitArea (self,area,new_dict,file) :
        if area == None :
            return

        self.linkdb.clear()
        #
        # FIND masks for TRANSIT lsas
        #
        for rtr in self.rtrlsa :
            for rlsa_t in self.rtrlsa[rtr]["TRANSIT"] :
                ip, mask = rlsa_t
                new_mask = 0
                #
                # mask currenlty holds designated router
                #
                for r in self.netlsa :
                    for nlsa in self.netlsa[r] :
                        i,m = nlsa
                        if ip & m == i and m > new_mask :   #kamila
                            new_mask = m 
                rlsa_t[1] = new_mask                 
        #            
        # Disable redundant STUB NETWORKS
        #        
        for rtr, rlsas in self.rtrlsa.items() :
            for rlsa_s in rlsas["STUB"] :
                ip, mask = rlsa_s
                for rlsa_t in rlsas["TRANSIT"] :
                    i,m = rlsa_t
                    if ip & mask == i & m :
                        # disable STUB lsa matching TRANSIT lsa
                        # within the same router
                        #print "mask "+id2str(ip)
                        #Debug_Print(debug_filename,"ip", id2str(i),'m', m, 'mask', mask)
                        rlsa_s[0] = 0
                    else:
                        pass
        
        for rtr,nlsas in self.netlsa.items() :
            for nlsa in nlsas :
                ip, mask = nlsa
                self.addLink(ip,mask,"NETWORK")
        
        for rtr,rlsas in self.rtrlsa.items() :
            for type in ("STUB","P2P","TRANSIT") :
                for rlsa in rlsas[type] :
                    ip, mask = rlsa
                    if ip == 0 :
                        continue
                    ip,mask = rlsa
                    if mask == 0:
                       pass
                    self.addLink(ip, mask, type)
        
        file.truncate()
        for (ip,mask), link in self.linkdb.items() :
            print >> self.dbf, link[0], id2str(ip), id2str(mask), link[1] ####file 
            Debug_Print(debug_filename, rtr, link[0], id2str(ip), id2str(mask), link[1] )
            if(link[1] != 'BROKEN') :        
                new_dict[id2str(ip)] = 'UP'
            else:
                new_dict[id2str(ip)] = 'DOWN'

        self.netlsa.clear()
        self.rtrlsa.clear()
        self.linkdb.clear()
        
    def load (self) :
        self.dbf.seek(0)
        self.linkdb.clear()
        self.netlsa.clear()
        self.rtrlsa.clear()

        for line in self.dbf :
            type, str_ip, str_mask, status = line.split()
            self.linkdb[str2id(str_ip),str2id(str_mask)] = [type,status]

    def checkLink (self,link_addr) :
        laddr = str2id(link_addr)
        
        PREF = "-"
        MODE = "-"
        MASK = 0
        
        for (ip,mask),link in self.linkdb.items() :
            type, mode = link
            best = False
            if ip == laddr :
                if MODE == "LINKED" :
                    if mode == "LINKED" and mask > MASK :
                        best = True
                else :
                    if mode == "LINKED" :
                        best = True
                    elif mask > MASK :
                        best = True
            if best: 
                PREF = id2str(ip) + "/" + str(mask2plen(mask))
                MODE = mode
                MASK = mask

        return (MODE == "LINKED", PREF,MODE)
    

################################################################################

global VERBOSE
'''
domains = {}
domain_binds = {}
'''
parser = argparse.ArgumentParser(description='Check OSPF link in lsadb')
parser.add_argument('--verbose', '-v', action='count', help="Be verbose")
#parser.add_argument('link_addr', help="link address to check")
parser.add_argument('param', help="link address to check or discovery mode")
args = parser.parse_args()

VERBOSE   = args.verbose
if VERBOSE > 0: Debug_Print(debug_filename,ospf)

mode = 'check_link'
link_addr = args.param

if (args.param == 'discovery'):
    mode = args.param
    link_addr = None

print('mode = ', mode)
ospf = Ospf()
old_dict = {}
new_dict = {}
string_list = []
mask        = 0

mask, domains, syslog_platform, sp, syslog_filename, debug_filename, zabbix_filename = Config_parse(mode, link_addr, mask) 
print('in ospflink', mask, domains, syslog_platform, sp, syslog_filename, debug_filename, zabbix_filename)
if (len(domains) == 0) :
    print >> sys.stderr, "domain did not matched in the cofig file"
    exit(1)

if mode == 'check_link':
    if syslog_platform != None:
        if syslog_platform == 'win':
            My_Logger = Win_Logger(sp)
            print('win')
        else:
            My_Logger = Lin_Logger(sp)

    if syslog_filename != None:
        My_Logger = File_Logger(syslog_filename)

lock_file = data_dir + '/common.lock'
if not os.path.exists(lock_file) :
        open(lock_file,"a").close()
lck = open(lock_file, "r+")

#################################################
#################################################
#################################################
for domain, agent_comm in domains.items() :
    print('DOMAIN', domain)
    print('AGENT COMMUNITY', agent_comm)
    #blocking file, only 1 process working now
    if platform.system() == "Windows" :
        start = time.time()
        sleep_time = 0.05
        while True :
            try :
                print('block')
                msvcrt.locking(lck.fileno(), msvcrt.LK_NBLCK, 1)
                print('do it')
            except IOError as error:
                now = time.time()
                #delay = now - start
                if now - start > LOCK_TIMEOUT :
                    print('strt', start)
                    print('now', now)
                    print('now - start', now - start)
                    print('timeout', LOCK_TIMEOUT)
                    print >> sys.stderr, "can not lock " + lock_file
                    exit(1)
                sleep_time = sleep_time*(1+random.random())
                if now + sleep_time - start > LOCK_TIMEOUT :
                    sleep_time = start + LOCK_TIMEOUT + 0.1 - now
                # print "==> %0.2f, %0.2f" % (sleep_time, now-start)
                time.sleep(sleep_time)
            else :
                print('all')
                break
    else :
        fcntl.flock(lck.fileno(), fcntl.LOCK_EX) 

    dbfile = data_dir + '\\' + domain + ".dat"

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
            print('agent', agent)
            print('comm', agent_comm['community'] )
            try :
                addr,port = agent.split(":") 
                print('addr', addr)       
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
                    exit(1)
            
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
            if (syslog_platform != None or syslog_filename != None):
                for s in string_list:
                    My_Logger.Log_Write(s)
    linkdb.load()
    
    if(mode == 'check_link'):
        (status, link, mode) = linkdb.checkLink(link_addr)
        descr = "("+",".join([domain, link, mode]) + ")"
        if status : 
            print ("UP")
        else :
            print ("DOWN")
    elif(mode == 'discovery'):
        Cash_Check (dbf, zabbix_filename)
 