class BrokenMessage(Exception):
    def __str__(self):
        raise RuntimeError("formatter failed")
def f():
    raise BrokenMessage()
