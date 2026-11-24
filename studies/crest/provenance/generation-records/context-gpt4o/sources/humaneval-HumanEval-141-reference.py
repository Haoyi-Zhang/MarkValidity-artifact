def file_name_check(file_name):
    if file_name.count('.') != 1:
        return 'No'
    prefix, suffix = file_name.split('.')
    if not prefix or not prefix[0].isalpha() or sum(c.isdigit() for c in file_name) > 3:
        return 'No'
    if suffix not in ['txt', 'exe', 'dll']:
        return 'No'
    return 'Yes'