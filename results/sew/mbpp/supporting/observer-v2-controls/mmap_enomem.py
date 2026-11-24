def f():
    import mmap
    return mmap.mmap(-1, 2**31)
