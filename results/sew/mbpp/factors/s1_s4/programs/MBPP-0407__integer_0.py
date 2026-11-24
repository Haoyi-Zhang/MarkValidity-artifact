def  rearrange_bigger(n):
    nums = list(str(n))
    for  i in  range(len(nums)-2,-1,-1):
        if nums[i]<nums[1+i]:
            z = nums[i:]
            y = min(filter(lambda  x: z[0] < x, z))
            z.remove(y)
            z.sort()
            nums[i:] = [y] + z
            return  int("".join(nums))
    return False