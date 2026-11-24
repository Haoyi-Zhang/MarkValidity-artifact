
    for word in words:
        words_list = word.split()
        p_words = [w for w in words_list if w.startswith('p') or w.startswith('P')]
        if len(p_words) == 2:
            return tuple(p_words)
    return None
