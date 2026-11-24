def comb_sort(nums):
    shrink_fact, gaps = 1.3, len(nums)
    swapped, i = True, 0
    while gaps>1 or swapped:
        gaps = int(float(gaps) / shrink_fact)
        swapped, i = False, 0
        while gaps + i<len(nums):
            if  nums[i] > nums[i+gaps]:
                nums[i], nums[gaps+i] = nums[gaps+i], nums[i]
                swapped = True
            i += 1
    return nums
