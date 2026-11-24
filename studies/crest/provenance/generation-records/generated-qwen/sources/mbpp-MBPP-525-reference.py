
def parallel_lines(line1, line2):
    if len(line1) == 2 and len(line2) == 2:
        return line1[0] / line1[1] == line2[0] / line2[1]
    else:
        return line1[0] == line2[0] and line1[1] == line2[1]
