import  sys
def next_smallest_palindrome(num):
    numstr=str(num)
    for i in range(1+num,sys.maxsize):
        if str(i) == str(i)[::-1]:
            return  i