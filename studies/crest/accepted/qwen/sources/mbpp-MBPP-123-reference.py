
def amicable_numbers_sum(limit):
    def proper_divisors_sum(n):
        divisors = [1]
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                divisors.append(i)
                if i != n // i:
                    divisors.append(n // i)
        return sum(divisors)

    amicable_sum = 0
    found_amicable = set()

    for num in range(2, limit + 1):
        if num not in found_amicable:
            d_num = proper_divisors_sum(num)
            if d_num != num and proper_divisors_sum(d_num) == num:
                amicable_sum += num + d_num
                found_amicable.add(num)
                found_amicable.add(d_num)

    return amicable_sum
