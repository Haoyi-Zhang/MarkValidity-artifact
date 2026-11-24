
  def Seq_Linear(seq_nums):
    if len(seq_nums) < 2:
      return "Linear Sequence"
    
    diff = seq_nums[1] - seq_nums[0]
    for i in range(2, len(seq_nums)):
      if seq_nums[i] - seq_nums[i-1] != diff:
        return "Non Linear Sequence"
    
    return "Linear Sequence"
