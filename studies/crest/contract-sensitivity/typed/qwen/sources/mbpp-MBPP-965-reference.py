
def camel_to_snake(text):
    snake_str = ''
    for char in text:
        if char.isupper():
            snake_str += '_' + char.lower()
        else:
            snake_str += char
    return snake_str[1:] if snake_str[0] == '_' else snake_str
