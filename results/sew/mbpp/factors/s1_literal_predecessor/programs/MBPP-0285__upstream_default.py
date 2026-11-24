import  re
def text_match_two_three(text):
        patterns = 'ab{2,3}'
        if not re.search(patterns,  text):
                return False
        else:
                return True
