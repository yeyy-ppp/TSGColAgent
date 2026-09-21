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
  def countVisitedNodes(self, edges: List[int]) -> List[int]:
    n = len(edges)
    ans = [0] * n
    inDegrees = [0] * n
    seen = [False] * n
    stack = []

    for v in edges:
      inDegrees[v] += 1

    q = collections.deque([i for i, d in enumerate(inDegrees) if d == 0])

    while q:
      u = q.popleft()
      inDegrees[edges[u]] -= 1
      if inDegrees[edges[u]] == 0:
        q.append(edges[u])
      stack.append(u)
      seen[u] = True

    for i in range(n):
      if not seen[i]:
        self._fillCycle(edges, i, seen, ans)

    while stack:
      u = stack.pop()
      ans[u] = ans[edges[u]] + 1

    return ans

  def _fillCycle(self, edges: List[int], start: int, seen: List[bool], ans: List[int]) -> None:
    cycleLength = 0
    u = start
    while not seen[u]:
      cycleLength += 1
      seen[u] = True
      u = edges[u]
    ans[start] = cycleLength
    u = edges[start]
    while u != start:
      ans[u] = cycleLength
      u = edges[u]
