#work with dictionaries
import os
from ospflink.debug_print import *

def Creating_Old_Dict( old_dict, my_file ):
    if os.path.exists(my_file) :
        Debug_Print("REOPENING cash FILE")
        cash_file = open(my_file, "r")
        for line in cash_file:
            l = line.split()
            if(l[len(l) - 1] != 'BROKEN'):
                old_dict[l[1]] = 'UP'
            else:
                old_dict[l[1]] = 'DOWN'
        cash_file.close()
    else:
        Debug_Print('new one')
    
def What_to_Write ( old_dict, new_dict, string_list ):
    Debug_Print('in what to write')
    for keys, values in old_dict.items():
        Debug_Print(keys, values)      
    if not old_dict:
        Debug_Print('old is empty')
        return
    for keys,values in new_dict.items():
        if keys not in old_dict.keys() or values != old_dict[keys]:
            string_list.append(keys + ' ' + values)
            Debug_Print('string', string_list)
        else:
            Debug_Print('already there')
            continue
    for keys,values in old_dict.items():
        if keys not in new_dict.keys():
            Debug_Print('turn into down')
            values = 'DOWN'
            string_list.append(keys + '   ' + values)
        else:
            Debug_Print('no need to do down')
            continue

