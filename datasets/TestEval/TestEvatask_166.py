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
  def getSubarrayBeauty(self, nums: List[int], k: int, x: int) -> List[int]:
    ans = []
    count = [0] * 50

    for i, num in enumerate(nums):
      if num < 0:
        count[num + 50] += 1
      if i - k >= 0 and nums[i - k] < 0:
        count[nums[i - k] + 50] -= 1
      if i + 1 >= k:
        ans.append(self._getXthSmallestNum(count, x))

    return ans

  def _getXthSmallestNum(self, count: List[int], x: int) -> int:
    prefix = 0
    for i in range(50):
      prefix += count[i]
      if prefix >= x:
        return i - 50
    return 0
