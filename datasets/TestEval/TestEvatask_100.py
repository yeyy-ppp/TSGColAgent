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
  def canDistribute(self, nums: List[int], quantity: List[int]) -> bool:
    freqs = list(collections.Counter(nums).values())
    validDistribution = self._getValidDistribution(freqs, quantity)
    n = len(freqs)
    m = len(quantity)
    maxMask = 1 << m
    dp = [[False] * maxMask for _ in range(n + 1)]
    dp[n][maxMask - 1] = True

    for i in range(n - 1, -1, -1):
      for mask in range(maxMask):
        dp[i][mask] = dp[i + 1][mask]
        availableMask = ~mask & (maxMask - 1)
        submask = availableMask
        while submask > 0:
          if validDistribution[i][submask]:
            dp[i][mask] = dp[i][mask] or dp[i + 1][mask | submask]
          submask = (submask - 1) & availableMask

    return dp[0][0]

  def _getValidDistribution(self, freqs: List[int], quantity: List[int]) -> List[List[bool]]:
    maxMask = 1 << len(quantity)
    validDistribution = [[False] * maxMask for _ in range(len(freqs))]
    for i, freq in enumerate(freqs):
      for mask in range(maxMask):
        if freq >= self._getQuantitySum(quantity, mask):
          validDistribution[i][mask] = True
    return validDistribution

  def _getQuantitySum(self, quantity: List[int], mask: int) -> int:
    res=[]
    for i, q in enumerate(quantity):
      if mask >> i & 1:
        res.append(q)
    return sum(res)
