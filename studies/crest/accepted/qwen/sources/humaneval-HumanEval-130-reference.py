
def tri(n):
    if n == 0:
        return [1]
    elif n == 1:
        return [1, 3]
    
    sequence = [1, 3]
    for i in range(2, n + 1):
        if i % 2 == 0:
            sequence.append(1 + i / 2)
        else:
            next_value = sequence[i - 1] + sequence[i - 2] + (sequence[-1] if len(sequence) > i else 0)
            sequence.append(next_value)
    
    return sequence
