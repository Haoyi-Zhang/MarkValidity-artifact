import  re
def text_match_wordz(text):
        patterns = '\w*z.\w*'
        if not re.search(patterns,  text):
                return False
        else:
                return True
