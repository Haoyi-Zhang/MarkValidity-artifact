def make_a_pile(n):
    pile = []
    current_stone = n
    for i in range(n):
        pile.append(current_stone)
        if current_stone % 2 == 0:
            current_stone += 2
        else:
            current_stone += 2
    return pile