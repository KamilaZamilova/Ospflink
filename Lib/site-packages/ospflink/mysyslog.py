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
        