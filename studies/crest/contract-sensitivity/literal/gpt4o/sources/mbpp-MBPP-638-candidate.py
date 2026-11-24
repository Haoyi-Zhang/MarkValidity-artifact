def wind_chill(v, t):
	return int(35.74 + t * 0.6215 - v ** 0.16 * 35.75 + t * 0.4275 * v ** 0.16)
