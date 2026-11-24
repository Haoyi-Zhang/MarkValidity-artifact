def  sum_average(number):
 total=0
 for value in range(1, number + 1):
    total=value + total
 average=total/number
 return  (total,average)