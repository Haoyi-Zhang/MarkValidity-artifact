
def get_row(lst, x):
    result = []
    for r, row in enumerate(lst):
        indices = [c for c, val in enumerate(row) if val == x]
        indices.sort(reverse=True)
        result.extend([(r, i) for i in indices])
    return sorted(result)
