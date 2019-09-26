#work with dictionaries
import os
from ospflink.debug_print import *

def Creating_Old_Dict( old_dict, cash_file ):
    cash_file.seek(0,0)
    for line in cash_file:
        l = line.split()
        if(l[len(l) - 1] != 'BROKEN'):
            old_dict[l[1]] = 'UP'
        else:
            old_dict[l[1]] = 'DOWN'

    
def What_to_Write ( old_dict, new_dict, string_list ):
    #for keys, values in old_dict.items():
        #Debug_Print(keys, values)      
    if not old_dict:
        return
    for keys,values in new_dict.items():
        if keys not in old_dict.keys() or values != old_dict[keys]:
            string_list.append(keys + ' ' + values)
        else:
            continue
    for keys,values in old_dict.items():
        if keys not in new_dict.keys():
            values = 'DOWN'
            string_list.append(keys + '   ' + values)
        else:
            continue

