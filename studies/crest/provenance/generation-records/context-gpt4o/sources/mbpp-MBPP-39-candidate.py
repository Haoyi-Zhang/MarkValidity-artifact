def rearange_string(S):
	from collections import Counter
	import heapq
	count = Counter(S)
	max_heap = [(-freq, char) for char, freq in count.items()]
	heapq.heapify(max_heap)
	prev_char = None
	prev_freq = 0
	result = []
	while max_heap or prev_freq:
		if prev_freq:
			if not max_heap:
				return ''
			heapq.heappush(max_heap, (prev_freq, prev_char))
		freq, char = heapq.heappop(max_heap)
		list.append(result, char)
		prev_char = char
		prev_freq = freq + 1
	return str.join('', result) if len(result) == len(S) else ''
