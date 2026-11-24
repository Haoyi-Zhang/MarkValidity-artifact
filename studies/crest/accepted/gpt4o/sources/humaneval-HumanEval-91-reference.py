def is_bored(S):
    import re
    sentences = re.split('[.!?]', S)
    return sum(1 for sentence in sentences if sentence.strip().startswith('I'))