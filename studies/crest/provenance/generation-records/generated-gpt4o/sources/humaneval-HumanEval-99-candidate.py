from decimal import Decimal, ROUND_HALF_UP


def closest_integer(value):
	decimal_value = Decimal(value)
	return int(decimal_value.to_integral_value(rounding=ROUND_HALF_UP))
