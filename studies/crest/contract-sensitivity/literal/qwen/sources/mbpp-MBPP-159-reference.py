
    seasons = {
        'January': 'winter',
        'February': 'winter',
        'March': ['winter', 'spring'],
        'April': 'spring',
        'May': 'spring',
        'June': ['spring', 'summer'],
        'July': 'summer',
        'August': 'summer',
        'September': ['summer', 'autumn'],
        'October': 'autumn',
        'November': 'autumn',
        'December': ['autumn', 'winter']
    }
    
    if isinstance(seasons[month], list):
        if days > 20:
            return seasons[month][1]
        else:
            return seasons[month][0]
    else:
        return seasons[month]
