
def check_String(str):
    has_letter = False
    has_number = False
    for char in str:
        if char.isalpha():
            has_letter = True
        elif char.isdigit():
            has_number = True
    return has_letter and has_number
