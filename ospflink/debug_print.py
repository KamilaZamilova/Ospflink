
from global_var import *

config_file = root_dir + "/ospflink.cfg"
cf = open(config_file, 'r')

def Debug_Print( file_name, *args): 
    if (file_name != None) : 
        debug_file = open(file_name,'a')
        for arg in args:
            debug_file.write(str(arg) + '  ')
        debug_file.write('\n')
        debug_file.close()
        