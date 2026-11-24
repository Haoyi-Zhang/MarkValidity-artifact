
def k_smallest_pairs(nums1, nums2, k):
    import heapq
    min_heap = []
    
    for i in range(min(len(nums1), k)):
        for j in range(min(len(nums2), k)):
            if len(min_heap) < k:
                heapq.heappush(min_heap, (-(nums1[i] + nums2[j]), nums1[i], nums2[j]))
            elif -(nums1[i] + nums2[j]) > min_heap[0][0]:
                heapq.heapreplace(min_heap, (-(nums1[i] + nums2[j]), nums1[i], nums2[j]))
    
    return [[pair[1], pair[2]] for pair in min_heap]
