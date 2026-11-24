def split_words(txt):
    if ' ' in txt:
        return txt.split()
    elif ',' in txt:
        return txt.split(',')
    else:
        odd_order_count = sum(1 for c in txt if 'a' <= c <= 'z' and (ord(c) - ord('a')) % 2 == 1)
        return odd_order_count