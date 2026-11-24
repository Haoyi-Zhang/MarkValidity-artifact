import heapq
def  k_smallest_pairs(nums1, nums2, k):
   queue=list()
   def  push(i, j):
       if  i < len(nums1) and  j < len(nums2):
           heapq.heappush(queue, [nums1[i] + nums2[j], i, j])
   push(0, 0)
   pairs=list()
   while queue and len(pairs) < k:
       _, i, j = heapq.heappop(queue)
       pairs.append([nums1[i], nums2[j]])
       push(i, 1 + j)
       if  0 == j:
           push(1 + i, 0)
   return pairs