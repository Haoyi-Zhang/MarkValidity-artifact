from collections import defaultdict
def  count_Substrings(s):
    n=len(s)
    count,sum=0,0
    mp=defaultdict(lambda : 0)
    mp[0]+=1
    for i in range(n):
        sum+=ord(s[i])-ord('0')
        count+=mp[sum-(1 + i)]
        mp[sum-(1 + i)]+=1
    return  count