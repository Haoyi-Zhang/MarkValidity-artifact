
def same_order(l1, l2):
    common = [x for x in l1 if x in l2]
    order_in_l1 = [l1.index(x) for x in common]
    order_in_l2 = [l2.index(x) for x in common]
    return all((order_in_l2[i] > order_in_l2[i-1] for i in range(1, len(order_in_l2))))
