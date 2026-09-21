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
  def minimumCost(self, start: List[int], target: List[int], specialRoads: List[List[int]]) -> int:
    return self.dijkstra(specialRoads, *start, *target)

  def dijkstra(self, specialRoads: List[List[int]], srcX: int, srcY: int, dstX: int, dstY: int) -> int:
    n = len(specialRoads)
    dist = [math.inf] * n
    minHeap = []

    for u, (x1, y1, _, _, cost) in enumerate(specialRoads):
      d = abs(x1 - srcX) + abs(y1 - srcY) + cost
      dist[u] = d
      heapq.heappush(minHeap, (dist[u], u))

    while minHeap:
      d, u = heapq.heappop(minHeap)
      if d > dist[u]:
        continue
      _, _, ux2, uy2, _ = specialRoads[u]
      for v in range(n):
        if v == u:
          continue
        vx1, vy1, _, _, vcost = specialRoads[v]
        newDist = d + abs(vx1 - ux2) + abs(vy1 - uy2) + vcost
        if newDist < dist[v]:
          dist[v] = newDist
          heapq.heappush(minHeap, (dist[v], v))

    ans = abs(dstX - srcX) + abs(dstY - srcY)
    for u in range(n):
      _, _, x2, y2, _ = specialRoads[u]
      ans = min(ans, dist[u] + abs(dstX - x2) + abs(dstY - y2))

    return ans
