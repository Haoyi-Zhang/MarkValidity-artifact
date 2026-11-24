
def remove(lst):
    return [''.join(filter(lambda c: not c.isdigit(), s)) for s in lst]
