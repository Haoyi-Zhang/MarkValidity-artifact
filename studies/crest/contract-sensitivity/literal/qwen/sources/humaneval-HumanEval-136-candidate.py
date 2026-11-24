
def largest_smallest_integers(lst):
	negatives = [x for x in lst if 0 > x]
	positives = [x for x in lst if 0 < x]

	largest_negative = max(negatives) if negatives else None
	smallest_positive = min(positives) if positives else None

	return (largest_negative, smallest_positive)
