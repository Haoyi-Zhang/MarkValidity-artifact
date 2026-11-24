
def anagram_lambda(texts, str):
    return list(filter(lambda x: sorted(x) == sorted(str), texts))
