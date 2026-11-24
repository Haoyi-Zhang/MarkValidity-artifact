
    from collections import Counter
    
    # Split all words in the list and count occurrences
    word_counts = Counter(' '.join(test_list).split())
    
    # Find the word with the maximum occurrences
    most_occurred_word = max(word_counts, key=word_counts.get)
    
    return most_occurred_word
