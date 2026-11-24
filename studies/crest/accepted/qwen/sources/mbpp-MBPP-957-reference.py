
import math

def get_First_Set_Bit_Pos(n):
    return int(math.log2(n & -n) + 1)
