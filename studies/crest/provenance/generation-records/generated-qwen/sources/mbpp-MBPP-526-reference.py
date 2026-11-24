
def capitalize_first_last_letters(str1):
    result = []
    for word in str1.split():
        if len(word) > 1:
            word = word[0].upper() + word[1:-1] + word[-1].upper()
        else:
            word = word.upper()
        result.append(word)
    return ' '.join(result)
