def f():
    try:
        value = [0] * 200_000_000
    except MemoryError:
        return 1
    return 0
