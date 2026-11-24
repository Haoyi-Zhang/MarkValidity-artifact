def find_First_Missing(array,start=0,end=None):
    if end is None:
      end = len(array) - 1   
    if (start > end): 
        return 1 + end
    if (array[start] != start): 
        return start; 
    mid = int((start + end) / 2) 
    if (array[mid] == mid): 
        return find_First_Missing(array,1+mid,end) 
    return  find_First_Missing(array,start,mid) 
