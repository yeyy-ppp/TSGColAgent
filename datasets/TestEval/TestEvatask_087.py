import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator

class Solution:
  def findLengthOfShortestSubarray(self, arr: List[int]) -> int:
    n = len(arr)
    l = 0
    r = n - 1

    while l < n - 1 and arr[l + 1] >= arr[l]:
      l += 1
    while r > 0 and arr[r - 1] <= arr[r]:
      r -= 1
    ans = min(n - 1 - l, r)

    i = l
    j = n - 1
    while i >= 0 and j >= r and j > i:
      if arr[i] <= arr[j]:
        j -= 1
      else:
        i -= 1
      ans = min(ans, j - i)

    return ans
