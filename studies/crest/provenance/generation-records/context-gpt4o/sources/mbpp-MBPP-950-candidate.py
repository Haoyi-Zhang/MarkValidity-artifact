def chinese_zodiac(year):
	index = (year - 1900) % 12
	zodiac_signs = ['Rat', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake', 'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']
	return zodiac_signs[index]
