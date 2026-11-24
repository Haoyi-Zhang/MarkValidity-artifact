def check_integer(text):
	text = text.strip()
	if not text:
		return None
	elif all(val in "0123456789" for (_, val) in enumerate(text)) or ((text[0] in "+-") and \
         all(text[i] in "0123456789" for i in range(1, len(text)))):
		return True
	else:
		return False
