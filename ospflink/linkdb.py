from ospflink.mutils import *
from ospflink.ospf import LSA_TYPES, RTR_LINK_TYPE

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
        
        #Debug_Print(debug_filename, rtr, type, lsid)
        
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
    