def  armstrong_number(number):
 sum = 0
 times, temp = 0, number
 while temp > 0:
           times = times + 1
           temp = temp // 10
 temp = number
 while temp > 0:
           reminder = temp % 10
           sum = sum + (reminder ** times)
           temp //= 10
 if not number == sum:
           return False
 else:
           return True
