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
  def numberOfWays(self, s: str, t: str, k: int) -> int:
    kMod = 1_000_000_007
    n = len(s)
    negOnePowK = 1 if k % 2 == 0 else -1  # (-1)^k
    z = self._zFunction(s + t + t)

    indices = [i - n for i in range(n, n + n) if z[i] >= n]
    dp = [0] * 2
    dp[1] = (pow(n - 1, k, kMod) - negOnePowK) * pow(n, kMod - 2, kMod)
    dp[0] = dp[1] + negOnePowK
    res = 0
    for index in indices:
      if index == 0:
        res += dp[0]
      else: 
        res += dp[1]
    return res % kMod


  def _zFunction(self, s: str) -> List[int]:
    n = len(s)
    z = [0] * n
    l = 0
    r = 0
    for i in range(1, n):
      if i < r:
        z[i] = min(r - i, z[i - l])
      while i + z[i] < n and s[z[i]] == s[i + z[i]]:
        z[i] += 1
      if i + z[i] > r:
        l = i
        r = i + z[i]
    return z
