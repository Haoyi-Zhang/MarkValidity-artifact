def pancake_sort(nums):
    arr_len=len(nums)
    while  arr_len>1:
        mi = nums.index(max(nums[:arr_len]))
        nums = nums[mi::-1] + nums[1+mi:len(nums)]
        nums = nums[arr_len - 1::-1] + nums[arr_len:len(nums)]
        arr_len -= 1
    return nums