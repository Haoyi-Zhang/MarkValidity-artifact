
def check(string):
    vowels = set("aeiouAEIOU")
    if vowels.issubset(set(string)):
        return 'accepted'
    else:
        return "not accepted"
