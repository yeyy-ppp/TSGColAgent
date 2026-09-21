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
  def reachableNodes(self, edges: List[List[int]], maxMoves: int, n: int) -> int:
    graph = [[] for _ in range(n)]
    dist = [maxMoves + 1] * n

    for u, v, cnt in edges:
      graph[u].append((v, cnt))
      graph[v].append((u, cnt))

    reachableNodes = self._dijkstra(graph, 0, maxMoves, dist)
    reachableSubnodes = 0

    for u, v, cnt in edges:
      a = 0 if dist[u] > maxMoves else min(maxMoves - dist[u], cnt)
      b = 0 if dist[v] > maxMoves else min(maxMoves - dist[v], cnt)
      reachableSubnodes += min(a + b, cnt)

    return reachableNodes + reachableSubnodes

  def _dijkstra(self, graph: List[List[Tuple[int, int]]], src: int, maxMoves: int, dist: List[int]) -> int:
    dist[src] = 0
    minHeap = [(dist[src], src)]

    while minHeap:
      d, u = heapq.heappop(minHeap)
      if dist[u] >= maxMoves:
        break
      if d > dist[u]:
        continue
      for v, w in graph[u]:
        newDist = d + w + 1
        if newDist < dist[v]:
          dist[v] = newDist
          heapq.heappush(minHeap, (newDist, v))

    return sum(d <= maxMoves for d in dist)
