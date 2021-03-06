from global_var import *
from mutils import plen2mask, str2id
import re, sys
import platform

config_file = root_dir + "/ospflink.cfg"
cf = open(config_file, 'r')

def Config_parse(mode, link_addr, mask):
    syslog_filename = None
    syslog_platform = None
    domains = {}
    #agents       = None
    #community   = None
    fsm = ""
    sp = ""
    archive_filename = ''
    for l in cf:
        l = l.lstrip()
        if re.search("^\s*#",l) : 
            continue
        if re.search("^\s*$",l) : 
            continue
        if l.startswith("[common]") :
            fsm = "common"
            continue
        if l.startswith("[domains]") :
            fsm = "domains"
            continue
        if l.startswith("[domain_binds]") :
            if fsm != "domains" :
                print >> sys.stderr, "section [domains] should be first in the cofig file"
                exit(1)                
            fsm = "domain_binds"
            continue
        if fsm == "common":
            m, r = l.split('=', 1)
            m = m.strip()
            r = r.strip()
            m = m.lower()
        
            if m == 'logger':
                t,a = r.split(':',1)
                t = t.strip()
                a = a.strip()
                if(t == 'file'):
                    if(a.startswith('\\') or a.startswith('/') ):
                        #My_Logger = File_Logger(a)
                        syslog_filename = a
                    else:
                        #My_Logger = File_Logger(data_dir + '/' + a)
                        syslog_filename = data_dir + '/' + a
                elif(t == 'syslog'):
                    if (platform.system() == "Windows" ):
                        syslog_platform = 'win'
                        sp = a
                        #My_Logger = Win_Logger(a)
                    elif (platform.system() == "Linux" ):
                        syslog_platform = 'lin'
                        sp = a
                        #My_Logger = Lin_Logger(a)
                    else:
                        print >> sys.stderr, 'Need to add a class for this OS '
                        exit(1)
                else:
                    print >> sys.stderr, 'Logging is only possible into a file or a syslog'
                    exit(1)
            elif m == 'lsdb_refresh_time':
                t, a = l.split('=', 1)
                a = a.strip()
                LSDB_REFRESH_TIME = a
            elif m == 'lock_timeout':
                t, a = l.split('=', 1)
                a = a.strip()
                LOCK_TIMEOUT = a
            elif m == 'debug':
                if(r.startswith('\\') or r.startswith('/') ):
                    debug_filename = r
                else:
                    debug_filename  = data_dir + '/' + r
            elif m == 'archive':
                if(r.startswith('\\') or r.startswith('/') ):
                    debug_filename = r
                else:
                    archive_filename  = data_dir + '/' + r
            else:
                print >> sys.stderr, 'Do not know how to process this argument : ', m
                exit(1)

   
        if fsm == "domains" :
            d,a,c =  l.split()
            domains[d]              = {}
            domains[d]["agents"]     = a
            domains[d]["community"] = c

            continue
        if fsm == "domain_binds" :
            p,d = l.split()
            n, m_l = p.split("/")
            m = plen2mask(int(m_l))

            if(mode == 'check_link'):
                if str2id(link_addr) & m == str2id(n) & m  and m >= mask :
                    mask        = m
                    for keys, values in domains.items():
                        if(keys != d):
                            domains.pop(keys)
                    fsm = ''
    return int(LSDB_REFRESH_TIME), int(LOCK_TIMEOUT), mask, domains, syslog_platform, sp, syslog_filename, debug_filename, archive_filename
    cf.close()