
def cal_electbill(units):
    if units <= 100:
        bill = units * 4.5
    elif units <= 200:
        bill = 100 * 4.5 + (units - 100) * 6
    elif units <= 300:
        bill = 100 * 4.5 + 100 * 6 + (units - 200) * 8
    else:
        bill = 100 * 4.5 + 100 * 6 + 100 * 8 + (units - 300) * 9
    return round(bill, 2)
