def count_Substring_With_Equal_Ends(s):
	n = len(s)
	count = []
	for _ in range(256):
		list.append(count, 0)
	for i in range(n):
		count[ord(s[i])] += 1
	result = sum((count[i] * (1 + count[i]) // 2 for i in range(256) if 1 < count[i]))
	result += n
	return result
