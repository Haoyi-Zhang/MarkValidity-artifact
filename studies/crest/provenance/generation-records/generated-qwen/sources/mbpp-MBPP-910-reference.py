
import calendar

def check_date(m, d, y):
    try:
        m = int(m)
        d = int(d)
        y = int(y)
        return 1 <= m <= 12 and 1 <= d <= calendar.monthrange(y, m)[1]
    except ValueError:
        return False
