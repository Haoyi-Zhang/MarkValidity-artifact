
def is_samepatterns(colors, patterns):
	if len(colors) != len(patterns):
		return False
    
	color_to_pattern = {}
	pattern_to_color = {}
    
	for color, pattern in zip(colors, patterns):
		if color not in color_to_pattern:
			color_to_pattern[color] = pattern
		if pattern not in pattern_to_color:
			pattern_to_color[pattern] = color
        
		if color_to_pattern[color] != pattern or pattern_to_color[pattern] != color:
			return False
    
	return True
