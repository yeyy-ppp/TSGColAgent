import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator

class IndexedQuery:
  def __init__(self, queryIndex: int, a: int, b: int):
    self.queryIndex = queryIndex
    self.a = a
    self.b = b

  def __iter__(self):
    yield self.queryIndex
    yield self.a
    yield self.b


class Solution:
  def leftmostBuildingQueries(self, heights: List[int], queries: List[List[int]]) -> List[int]:
    ans = [-1] * len(queries)
    stack = []

    heightsIndex = len(heights) - 1
    for queryIndex, a, b in sorted([IndexedQuery(i, min(a, b), max(a, b)) for i, (a, b) in enumerate(queries)], key=lambda iq: -iq.b):
      if a == b or heights[a] < heights[b]:
        ans[queryIndex] = b
      else:
        while heightsIndex > b:
          while stack and heights[stack[-1]] <= heights[heightsIndex]:
            stack.pop()
          stack.append(heightsIndex)
          heightsIndex -= 1
        j = self._lastGreater(stack, a, heights)
        if j != -1:
          ans[queryIndex] = stack[j]

    return ans

  def _lastGreater(self, A: List[int], target: int, heights: List[int]):
    l = -1
    r = len(A) - 1
    while l < r:
      m = (l + r + 1) // 2
      if heights[A[m]] > heights[target]:
        l = m
      else:
        r = m - 1
    return l
