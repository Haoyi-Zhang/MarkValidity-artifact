def anti_shuffle(s):
    def sort_chars(word):
        return ''.join(sorted(word))
    
    words = s.split(' ')
    sorted_words = [sort_chars(word) for word in words]
    return ' '.join(sorted_words)