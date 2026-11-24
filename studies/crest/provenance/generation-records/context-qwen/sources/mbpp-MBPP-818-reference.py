
def lower_ctr(str):
    count = 0
    for char in str:
        if char.islower():
            count += 1
    return count
