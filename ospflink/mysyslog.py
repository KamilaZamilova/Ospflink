#syslog creating and updating
import os
from datetime import datetime
import platform
if platform.system() == "Windows" :
    import win32api
    import win32con
    import win32evtlog
    import win32security
    import win32evtlogutil
if platform.system() == "Linux":
    import syslog

class Logger:

    def Log_Write(self, massive): pass
    def Close(self): pass

class File_Logger(Logger):

    def __init__(self, syslog_file):
        file = open(syslog_file,'a')
        self.file = file

    def Log_Write(self, string):
        a,b = string.split()
        self.file.write(datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S") + '    ' + a + '    ' + b + '\n')

    def Close(self):
        self.file.close()


class Win_Logger(Logger):

    def __init__(self, computer):
        logType = "Application"
        if computer == 'None':
            computer = None
        self.h = win32evtlog.OpenEventLog(computer , logType)

    def Log_Write(self, string):
        
        applicationName = "My Application"
        eventID = 1
        category = 5	# Shell
        myType = win32evtlog.EVENTLOG_WARNING_TYPE
        l = string.split()
        descr = ["A warning, link", l[0],  "changed its status into " , l[1]]
        data = "13453576".encode("ascii")

        win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, 
	            eventType=myType, strings=descr, data=data)
    
    def Close(self):
        win32evtlog.CloseEventLog(self.h) 

class Lin_Logger(Logger):
    def __init__(self, computer):
        syslog.openlog()
    def Log_Write(self, string):
        syslog.syslog(syslog.LOG_INFO, string)
    def Close(self):
        syslog.closelog()
        





'''
 def syslog_Begin(file, syslog_dict):
    if os.path.exists(file) :
        print("REOPENING cash FILE")
        cash_file = open(file, "r")
        for line in cash_file:
            l = line.split()
            if(l[len(l) - 1] != 'BROKEN'):
                #print('that is ok')
                syslog_dict[l[1]] = 'UP'
            else:
                print('not ok')
                syslog_dict[l[1]] = 'DOWN'
        cash_file.close()
    else:
        print('new one')

def syslog_Write (file,old_d,new_d):
    print('in write')
    syslog_file = open(file, "a")       
    if not old_d:
        print('old is empty')
        return

    for keys,values in new_d.items():
        if keys not in old_d.keys() or values != old_d[keys]:
            #print(keys, values, old_d[keys])
        #if values != old_d[keys]:
            print('write into file')
            Write_into_file(syslog_file,keys,values)
        else:
            print('already there')
            continue
    for keys,values in old_d.items():
        if keys not in new_d.keys():
            print('change to down')
            values = 'DOWN'
            Write_into_file(syslog_file,keys,values)
        else:
            print('no need to do down')
            continue
    syslog_file.close()
        
def Write_into_syslog(computer = None, logType="Application",key,value):
    h=win32evtlog.OpenEventLog(computer, logType)
    #numRecords = win32evtlog.GetNumberOfEventLogRecords(h)
    #print "There are %d records" % numRecords

    #file.write(datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S") + '   {}   {}\n'.format(key,value))
    applicationName = "My Application"
    eventID = 1
    category = 5	# Shell
    myType = win32evtlog.EVENTLOG_WARNING_TYPE
    descr = ["A warning", "An even more dire warning"]
    data = "Application\0Data".encode("ascii")
 
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, 
	eventType=myType, strings=descr, data=data, sid=my_sid)
'''
