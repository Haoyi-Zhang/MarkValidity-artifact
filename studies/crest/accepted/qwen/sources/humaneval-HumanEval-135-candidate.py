
return next((i for i in range(len(arr) - 1, 0, -1) if arr[i - 1] > arr[i]), -1)
