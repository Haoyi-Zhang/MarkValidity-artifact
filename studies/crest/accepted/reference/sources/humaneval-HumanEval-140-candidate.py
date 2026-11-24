
def fix_spaces(text):
	"""
    Given a string text, replace all spaces in it with underscores, 
    and if a string has more than 2 consecutive spaces, 
    then replace all consecutive spaces with - 
    
    fix_spaces("Example") == "Example"
    fix_spaces("Example 1") == "Example_1"
    fix_spaces(" Example 2") == "_Example_2"
    fix_spaces(" Example   3") == "_Example-3"
    """
	start = 0
	end = 0
	new_text = ""
	i = 0
	while i < len(text):
		if text[i] == " ":
			end += 1
		else:
			if 2 < end - start:
				new_text += text[i] + "-"
			elif 0 < end - start:
				new_text += (end - start) * "_" + text[i]
			else:
				new_text += text[i]
			start = i + 1
			end = i + 1
		i += 1
	if 2 < end - start:
		new_text += "-"
	elif 0 < end - start:
		new_text += "_"
	return new_text
