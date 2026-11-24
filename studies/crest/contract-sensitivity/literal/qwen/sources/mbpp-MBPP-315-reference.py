
def find_Max_Len_Even(str):
    words = str.split()
    max_len_even_word = ""
    
    for word in words:
        if len(word) % 2 == 0 and len(word) > len(max_len_even_word):
            max_len_even_word = word
    
    return max_len_even_word if max_len_even_word else "-1"
