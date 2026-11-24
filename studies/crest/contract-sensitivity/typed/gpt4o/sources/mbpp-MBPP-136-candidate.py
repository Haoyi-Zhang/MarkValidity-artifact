def cal_electbill(units):
	amount = units * 3.5 if units <= 100 else (100 * 3.5 + (units - 100) * 5 if units <= 200 else 100 * 3.5 + 5 * 100 + (units - 200) * 7)
	fixed_charge = 50
	return amount + fixed_charge
