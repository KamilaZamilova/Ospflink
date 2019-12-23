from datetime import datetime
import os
import json

def Cash_Check (dbf, zabbix_filename, dom):
    router_id = '0.0.0.0'
    delete_list = []
    add_list = {}
    dbf.seek(0,0)
    zabbix = open(zabbix_filename, 'a+')
    # in cash file
    for line1 in dbf:
        l1 = line1.split()
        if l1[3]!= 'BROKEN':
            l1[3] = 'UP'
        else : l1[3] = 'DOWN'
        flag = 0
        zabbix.seek(0,0)
        for line_no, line2 in enumerate(zabbix):
            l2 = line2.split()
            if (l1[1] == l2[0]):
                flag = 1
                if(l1[3] != l2[2] and dom == l2[4]):
                    delete_list.append(line_no)
                    add_list[l1[1]] = l1[3]
                    break
                break
        if(flag == 0):
            add_list[l1[1]] = l1[3]
        if (os.stat(zabbix_filename).st_size == 0):
            add_list[l1[1]] = l1[3]
    # in zabbix file
    zabbix.seek(0,0)
    dbf.seek(0,0)
    for line_no, line2 in enumerate(zabbix) :
        l2 = line2.split()
        flag = 0
        dbf.seek(0,0)
        for line1 in dbf:
            l1 = line1.split()
            if (l1[1] == l2[0] ):
                flag = 1
                break
        if (flag == 0):
            if(l2[2]!= 'DELETED' and dom == l2[4]):
                delete_list.append(line_no)
                add_list[l2[0]] = 'DELETED'

    if(len(delete_list)!= 0):
        Delete_Strings(zabbix, delete_list)
    for keys, values in add_list.items():
        Add_Into_Zabbix(zabbix, keys, router_id, values, dom)
    zabbix.close()

def Delete_Strings(file, my_list):
    file.seek(0,0)
    m = file.readlines()
    k = 0
    for i in my_list:
        m.pop(i-k)
        k +=1
    file.truncate(0)
    file.writelines(m)

def Add_Into_Zabbix( file, keys, router_id, values, dom): 
    s1 =  '{0:16}  {1:15}  {2:7}'.format(keys, router_id, values)
    s = s1 + '   ' + datetime.strftime(datetime.now(), "%d.%m.%Y_%H:%M:%S") + '   ' + dom
    file.write (s + '\n')

def Json_Fill(zabbix_filename):
    zabbix = open(zabbix_filename, 'r')
    list_of_objects = []
    for line in zabbix:
       l = line.split()
       s = {}
       s["{#USER}"] = l[0]
       list_of_objects.append(s)
    data = {}
    data["data"] = list_of_objects
    print(json.dumps(data))
    zabbix.close()