
import re


def change_date_format(dt):
	return re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\3-\2-\1', dt)
