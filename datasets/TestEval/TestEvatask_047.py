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
  def splitArraySameAverage(self, nums: List[int]) -> bool:
    n = len(nums)
    summ = sum(nums)
    if not any(i * summ % n == 0 for i in range(1, n // 2 + 1)):
      return False

    sums = [set() for _ in range(n // 2 + 1)]
    sums[0].add(0)

    for num in nums:
      for i in range(n // 2, 0, -1):
        for val in sums[i - 1]:
          sums[i].add(num + val)

    for i in range(1, n // 2 + 1):
      if i * summ % n == 0 and i * summ // n in sums[i]:
        return True

    return False
