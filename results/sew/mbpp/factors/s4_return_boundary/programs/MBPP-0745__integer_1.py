def  divisible_by_digits(startnum, endnum):
    return  [n for  n in  range(startnum, 1+endnum) \
                if  not  any(map(lambda  x: 0 == int(x) or  0 != n%int(x), str(n)))]