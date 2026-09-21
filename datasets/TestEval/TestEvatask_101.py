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
  def __init__(self):
    self.kMaxNum = 16

  def minimumIncompatibility(self, nums: List[int], k: int) -> int:
    kMaxCompatibility = (16 - 1) * (16 // 2)
    n = len(nums)
    subsetSize = n // k
    maxMask = 1 << n
    incompatibilities = self._getIncompatibilities(nums, subsetSize)

    dp = [kMaxCompatibility] * maxMask
    dp[0] = 0

    for mask in range(1, maxMask):
      if mask.bit_count() % subsetSize != 0:
        continue
      submask = mask
      while submask > 0:
        if incompatibilities[submask] != -1:
          dp[mask] = min(dp[mask], dp[mask - submask] + incompatibilities[submask])
        submask = (submask - 1) & mask

    if dp[-1] != kMaxCompatibility:
      return dp[-1]
    else:
      return -1

  def _getIncompatibilities(self, nums: List[int], subsetSize: int) -> List[int]:
    maxMask = 1 << len(nums)
    incompatibilities = [-1] * maxMask
    for mask in range(maxMask):
      if mask.bit_count() == subsetSize and self._isUnique(nums, mask, subsetSize):
        incompatibilities[mask] = self._getIncompatibility(nums, mask)
    return incompatibilities

  def _isUnique(self, nums: List[int], mask: int, subsetSize: int) -> bool:
    used = 0
    for i, num in enumerate(nums):
      if mask >> i & 1:
        used |= 1 << num
    return used.bit_count() == subsetSize

  def _getIncompatibility(self, nums: List[int], mask: int) -> int:
    mini = self.kMaxNum
    maxi = 0
    for i, num in enumerate(nums):
      if mask >> i & 1:
        maxi = max(maxi, num)
        mini = min(mini, num)
    return maxi - mini
