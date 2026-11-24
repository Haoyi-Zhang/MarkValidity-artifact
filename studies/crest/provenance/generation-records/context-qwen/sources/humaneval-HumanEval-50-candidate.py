
return str.join("", [chr(ord("a") + ((ord(ch) - 5 - ord("a")) % 26)) for ch in s])
