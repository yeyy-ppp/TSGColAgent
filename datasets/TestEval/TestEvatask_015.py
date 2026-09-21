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
  def countRangeSum(self, nums: List[int], lower: int, upper: int) -> int:
    n = len(nums)
    self.ans = 0
    prefix = [0] + list(itertools.accumulate(nums))

    self._mergeSort(prefix, 0, n, lower, upper)
    return self.ans

  def _mergeSort(self, prefix: List[int], l: int, r: int, lower: int, upper: int) -> None:
    if l >= r:
      return

    m = (l + r) // 2
    self._mergeSort(prefix, l, m, lower, upper)
    self._mergeSort(prefix, m + 1, r, lower, upper)
    self._merge(prefix, l, m, r, lower, upper)

  def _merge(self, prefix: List[int], l: int, m: int, r: int, lower: int, upper: int) -> None:
    lo = m + 1
    hi = m + 1

    for i in range(l, m + 1):
      while lo <= r and prefix[lo] - prefix[i] < lower:
        lo += 1
      while hi <= r and prefix[hi] - prefix[i] <= upper:
        hi += 1
      self.ans += hi - lo

    sorted = [0] * (r - l + 1)
    k = 0
    i = l
    j = m + 1

    while i <= m and j <= r:
      if prefix[i] < prefix[j]:
        sorted[k] = prefix[i]
        k += 1
        i += 1
      else:
        sorted[k] = prefix[j]
        k += 1
        j += 1

    while i <= m:
      sorted[k] = prefix[i]
      k += 1
      i += 1

    while j <= r:
      sorted[k] = prefix[j]
      k += 1
      j += 1

    prefix[l:l + len(sorted)] = sorted
