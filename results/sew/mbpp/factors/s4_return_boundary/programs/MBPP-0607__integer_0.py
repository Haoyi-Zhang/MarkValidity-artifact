import re


def find_literals(text, pattern):
  match=re.search(pattern, text)
  s, e = match.start(), match.end()
  return match.re.pattern, s, e