
def decimal_to_Octal(deciNum):
    if deciNum == 0:
        return 0
    octal = ""
    while deciNum > 0:
        remainder = deciNum % 8
        octal = str(remainder) + octal
        deciNum = deciNum // 8
    return int(octal)
