
def last_occurence_char(string, char):
    try:
        return string.rindex(char)
    except ValueError:
        return None
