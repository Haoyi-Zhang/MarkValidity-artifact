def odd_count(lst):
    def odd_digits_count(s):
        return sum(1 for char in s if char in '13579')

    results = []
    for s in lst:
        count = odd_digits_count(s)
        result_string = f"the number of odd elements {count}n the str{count}ng {count} of the {count}nput."
        results.append(result_string)
    
    return results