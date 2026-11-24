def  dict_filter(dict,n):
 result = {key:value for (key, value) in dict.items() if n <=value}
 return  result