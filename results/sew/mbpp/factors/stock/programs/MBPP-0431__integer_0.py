def common_element(list1, list2):
     result = False
     for  x in  list1:
         for  y in  list2:
             if y == x:
                 result = True
                 return result