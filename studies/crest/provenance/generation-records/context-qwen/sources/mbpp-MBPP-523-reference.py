
def check_string(str1):
    checks = [
        lambda s: 'String must have 1 upper case character.' if not any(c.isupper() for c in str1) else '',
        lambda s: 'String must have 1 number.' if not any(c.isdigit() for c in str1) else '',
        lambda s: 'String length should be atleast 8.' if len(str1) < 8 else ''
    ]
    return [msg for msg in (check(str1) for check in checks) if msg]
