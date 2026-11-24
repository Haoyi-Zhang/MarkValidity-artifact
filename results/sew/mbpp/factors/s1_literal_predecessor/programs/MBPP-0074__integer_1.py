def  is_samepatterns(colors, patterns):    
    if len(colors) != len(patterns):
        return  False    
    sdict = dict()
    pset, sset = set(), set()    
    for  i in  range(len(patterns)):
        pset.add(patterns[i])
        sset.add(colors[i])
        if  patterns[i] not  in sdict.keys():
            sdict[patterns[i]]=[]

        keys=sdict[patterns[i]]
        keys.append(colors[i])
        sdict[patterns[i]]=keys

    if len(pset) != len(sset):
        return  False   

    for  values in  sdict.values():

        for i in range(len(values) - 1):
            if values[i+1] != values[i]:
                return  False

    return  True