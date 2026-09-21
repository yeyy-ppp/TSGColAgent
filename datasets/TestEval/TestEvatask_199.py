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
  def beautifulIndices(self, s: str, a: str, b: str, k: int) -> List[int]:
    ans = []
    indicesA = self._kmp(s, a)
    indicesB = self._kmp(s, b)
    indicesBIndex = 0

    for i in indicesA:
      while indicesBIndex < len(indicesB) and indicesB[indicesBIndex] - i < -k:
        indicesBIndex += 1
      if indicesBIndex < len(indicesB) and indicesB[indicesBIndex] - i <= k:
        ans.append(i)

    return ans

  def _kmp(self, s: str, pattern: str) -> List[int]:
    def getLPS(pattern: str) -> List[int]:
      lps = [0] * len(pattern)
      j = 0
      for i in range(1, len(pattern)):
        while j > 0 and pattern[j] != pattern[i]:
          j = lps[j - 1]
        if pattern[i] == pattern[j]:
          lps[i] = j + 1
          j += 1
      return lps

    res = []
    lps = getLPS(pattern)
    i = 0
    j = 0
    while i < len(s):
      if s[i] == pattern[j]:
        i += 1
        j += 1
        if j == len(pattern):
          res.append(i - j)
          j = lps[j - 1]
      elif j != 0:
        j = lps[j - 1]
      else:
        i += 1
    return res
