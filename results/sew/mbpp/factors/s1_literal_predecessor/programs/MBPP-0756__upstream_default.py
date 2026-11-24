import  re
def text_match_zero_one(text):
        patterns = 'ab+?'
        if not re.search(patterns,  text):
                return False
        else:
                return True
