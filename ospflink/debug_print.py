
import global_var
config_file = global_var.workdir + "/ospflink.cfg"
cf = open(config_file, 'r')

for l in cf:
    l = l.lstrip()
    if l.startswith("[common]") :
        fsm = "common"
        continue
    if fsm == "common":
        m, r = l.split('=', 1)
        m = m.strip()
        r = r.strip()
        m = m.lower()
        if m == 'debug':
            if(r.startswith('\\') or r.startswith('/') ):
                file_name = r
            else:
                file_name = global_var.workdir + '/' + r
            break

debug_file = open(file_name,'w').close()

def Debug_Print( *args):      
    debug_file = open(file_name,'a')
    for arg in args:
        debug_file.write(str(arg) + '  ')
    debug_file.write('\n')
    debug_file.close()
        