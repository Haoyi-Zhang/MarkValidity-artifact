def min_flip_to_make_string_alternate(str):
    def flip(char):
        return '1' if char == '0' else '0'

    def count_flips(start):
        flips = 0
        expected_char = start
        for char in str:
            if char != expected_char:
                flips += 1
            expected_char = flip(expected_char)
        return flips

    return min(count_flips('0'), count_flips('1'))