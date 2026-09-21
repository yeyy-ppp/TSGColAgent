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
  def countSubgraphsForEachDiameter(self, n: int, edges: List[List[int]]) -> List[int]:
    maxMask = 1 << n
    dist = self._floydWarshall(n, edges)
    ans = [0] * (n - 1)

    for mask in range(maxMask):
      maxDist = self._getMaxDist(mask, dist, n)
      if maxDist > 0:
        ans[maxDist - 1] += 1

    return ans

  def _floydWarshall(self, n: int, edges: List[List[int]]) -> List[List[int]]:
    dist = [[n] * n for _ in range(n)]

    for i in range(n):
      dist[i][i] = 0

    for u, v in edges:
      dist[u - 1][v - 1] = 1
      dist[v - 1][u - 1] = 1

    for k in range(n):
      for i in range(n):
        for j in range(n):
          dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist

  def _getMaxDist(self, mask: int, dist: List[List[int]], n: int) -> int:
    maxDist = 0
    edgeCount = 0
    cityCount = 0
    for u in range(n):
      if (mask >> u) & 1 == 0:
        continue
      cityCount += 1
      for v in range(u + 1, n):
        if (mask >> v) & 1 == 0:
          continue
        if dist[u][v] == 1:
          edgeCount += 1
        maxDist = max(maxDist, dist[u][v])

    if edgeCount == cityCount - 1:
      return maxDist
    else:
      return 0
