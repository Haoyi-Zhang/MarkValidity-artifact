def amicable_numbers_sum(limit):
    if  not  isinstance(limit, int):
        return  "Input is not an integer!"
    if  limit < 1:
        return  "Input must be bigger than 0!"
    amicables = set()
    for num in range(2, limit+1):
        if num in amicables:
            continue
        sum_fact=sum([fact for fact in range(1, num) if num % fact == 0])
        sum_fact2=sum([fact for fact in range(1, sum_fact) if sum_fact % fact == 0])
        if sum_fact2 == num and sum_fact != num:
            amicables.add(num)
            amicables.add(sum_fact2)
    return  sum(amicables)
