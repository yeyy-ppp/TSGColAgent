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
  def maximumScore(self, nums: List[int], k: int) -> int:
    ans = 0
    stack = []

    for i in range(len(nums) + 1):
      while stack and (i == len(nums) or nums[stack[-1]] > nums[i]):
        h = nums[stack.pop()]
        w = i - stack[-1] - 1 if stack else i
        if (not stack or stack[-1] + 1 <= k) and i - 1 >= k:
          ans = max(ans, h * w)
      stack.append(i)

    return ans
