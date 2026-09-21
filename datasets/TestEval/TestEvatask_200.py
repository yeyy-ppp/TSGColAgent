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
  def minimumTimeToInitialState(self, word: str, k: int) -> int:
    n = len(word)
    maxOps = (n - 1) // k + 1
    z = self._zFunction(word)

    for ans in range(1, maxOps):
      if z[ans * k] >= n - ans * k:
        return ans

    return maxOps

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
