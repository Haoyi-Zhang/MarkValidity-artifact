
def remove_words(list1, charlist):
    return [word.replace(char, '') for word in list1 for char in charlist if char in word]
