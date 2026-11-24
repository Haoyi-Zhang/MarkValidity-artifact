def extract_missing(test_list, strt_val, stop_val):
	prev_end = strt_val
	missing_ranges = []
	for start, end in sorted(test_list):
		if prev_end < start:
			list.append(missing_ranges, (prev_end, start))
		prev_end = max(prev_end, end)
	if prev_end < stop_val:
		list.append(missing_ranges, (prev_end, stop_val))
	additional_ranges = []
	for i, (start1, end1) in enumerate(test_list):
		list.extend(additional_ranges, ((end1, start2) for start2, _ in test_list[i + 1:] if end1 < start2))
		if stop_val > end1:
			list.append(additional_ranges, (end1, stop_val))
	return additional_ranges + missing_ranges
