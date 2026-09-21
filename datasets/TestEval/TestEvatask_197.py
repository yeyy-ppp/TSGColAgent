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
  def canMakePalindromeQueries(self, s: str, queries: List[List[int]]) -> List[bool]:
    n = len(s)
    mirroredDiffs = self._getMirroredDiffs(s)
    counts = self._getCounts(s)
    ans = []

    def subtractArrays(a: List[int], b: List[int]):
      return [x - y for x, y in zip(a, b)]

    for a, b, c, d in queries:
      b += 1
      d += 1
      ra = n - a
      rb = n - b
      rc = n - c
      rd = n - d

      if (min(a, rd) > 0 and mirroredDiffs[min(a, rd)] > 0) or (n // 2 > max(b, rc) and mirroredDiffs[n // 2] - mirroredDiffs[max(b, rc)] > 0) or (rd > b and mirroredDiffs[rd] - mirroredDiffs[b] > 0) or (a > rc and mirroredDiffs[a] - mirroredDiffs[rc] > 0):
        ans.append(False)
      else:
        leftRangeCount = subtractArrays(counts[b], counts[a])
        rightRangeCount = subtractArrays(counts[d], counts[c])
        if a > rd:
          rightRangeCount = subtractArrays(
              rightRangeCount, subtractArrays(counts[min(a, rc)], counts[rd]))
        if rc > b:
          rightRangeCount = subtractArrays(
              rightRangeCount, subtractArrays(counts[rc], counts[max(b, rd)]))
        if c > rb:
          leftRangeCount = subtractArrays(
              leftRangeCount, subtractArrays(counts[min(c, ra)], counts[rb]))
        if ra > d:
          leftRangeCount = subtractArrays(
              leftRangeCount, subtractArrays(counts[ra], counts[max(d, rb)]))
        ans.append(min(leftRangeCount) >= 0
                   and min(rightRangeCount) >= 0
                   and leftRangeCount == rightRangeCount)

    return ans

  def _getMirroredDiffs(self, s: str) -> List[int]:
    diffs = [0]
    for i, j in zip(range(len(s)), reversed(range(len(s)))):
      if i >= j:
        break
      diffs.append(diffs[-1] + (s[i] != s[j]))
    return diffs

  def _getCounts(self, s: str) -> List[List[int]]:
    count = [0] * 26
    counts = [count.copy()]
    for c in s:
      count[ord(c) - ord('a')] += 1
      counts.append(count.copy())
    return counts
