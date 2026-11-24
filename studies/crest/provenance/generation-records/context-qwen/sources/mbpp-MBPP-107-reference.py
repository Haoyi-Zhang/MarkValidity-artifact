
def count_Hexadecimal(L,R) :
    return sum(1 for i in range(L, R+1) if hex(i).startswith('0x'))
