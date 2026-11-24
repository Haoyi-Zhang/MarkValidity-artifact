import  re
def text_lowercase_underscore(text):
        patterns = '^[a-z]+_[a-z]+$'
        if not re.search(patterns,  text):
                return False
        else:
                return True
