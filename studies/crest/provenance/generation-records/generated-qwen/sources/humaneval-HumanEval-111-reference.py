def histogram(test): 
    if not test: 
        return {} 
    letters = test.split() 
    freq = {} 
    for letter in letters: 
        if letter in freq: 
            freq[letter] += 1 
        else: 
            freq[letter] = 1 
    max_count = max(freq.values()) 
    result = {letter: count for letter, count in freq.items() if count == max_count} 
    return result