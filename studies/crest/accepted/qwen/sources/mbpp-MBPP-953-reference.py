
    # Create a dictionary to count occurrences of each element
    count_dict = {}
    for num in ar:
        if num in count_dict:
            count_dict[num] += 1
        else:
            count_dict[num] = 1
    
    # Find the maximum occurrence of any element
    max_count = max(count_dict.values())
    
    return max_count

# Test cases
print(subset([1, 2, 3, 4], 4))  # Output: 1
print(subset([5, 6, 9, 3, 4, 3, 4], 7))  # Output: 2
print(subset([1, 2, 3], 3))  # Output: 1
