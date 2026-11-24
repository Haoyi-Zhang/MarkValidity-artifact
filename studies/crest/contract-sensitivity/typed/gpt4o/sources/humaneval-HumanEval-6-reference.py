def parse_nested_parens(paren_string: str) -> List[int]:
    def max_nesting(paren_group: str) -> int:
        max_depth, current_depth = 0, 0
        for char in paren_group:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        return max_depth

    return [max_nesting(group) for group in paren_string.split()]