
import re

def is_valid_URL(str):
    regex = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
    if(re.search(regex,str)):
        return True
    else:
        return False
