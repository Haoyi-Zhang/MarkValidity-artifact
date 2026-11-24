import math


def wind_chill(v, t):
	windchill = 13.12 + t * 0.6215 -  math.pow(v, 0.16) * 11.37 + t * 0.3965 * math.pow(v, 0.16)
	return int(round(windchill, 0))
