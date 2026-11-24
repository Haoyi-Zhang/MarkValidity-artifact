def  convert_list_dictionary(l1, l2, l3):
     result = []
     for (x, y, z) in zip(l1, l2, l3):
         result.append({x: {y: z}})
     return  result