
def cal_electbill(units):
	bill = units * 4.5 if units <= 100 else (100 * 4.5 + (units - 100) * 6 if units <= 200 else (100 * 4.5 + 6 * 100 + (units - 200) * 8 if units <= 300 else 100 * 4.5 + 6 * 100 + 100 * 8 + (units - 300) * 9))
	return round(bill, 2)
