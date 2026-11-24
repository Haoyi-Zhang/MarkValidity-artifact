
def find_max(words):
    max_unique_word = ""
    max_unique_count = 0
    for word in words:
        unique_chars = set(word)
        if len(unique_chars) > max_unique_count or (len(unique_chars) == max_unique_count and word < max_unique_word):
            max_unique_word = word
            max_unique_count = len(unique_chars)
    return max_unique_word
