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
  def minimumWeight(self, n: int, edges: List[List[int]], src1: int, src2: int, dest: int) -> int:
    graph = [[] for _ in range(n)]
    reversedGraph = [[] for _ in range(n)]

    for u, v, w in edges:
      graph[u].append((v, w))
      reversedGraph[v].append((u, w))

    fromSrc1 = self._dijkstra(graph, src1)
    fromSrc2 = self._dijkstra(graph, src2)
    fromDest = self._dijkstra(reversedGraph, dest)
    minWeight = min(a + b + c for a, b, c in zip(fromSrc1, fromSrc2, fromDest))
    if minWeight == math.inf:
      return -1
    else:
      return minWeight

  def _dijkstra(self, graph: List[List[Tuple[int, int]]], src: int) -> List[int]:
    dist = [math.inf] * len(graph)

    dist[src] = 0
    minHeap = [(dist[src], src)]

    while minHeap:
      d, u = heapq.heappop(minHeap)
      if d > dist[u]:
        continue
      for v, w in graph[u]:
        if d + w < dist[v]:
          dist[v] = d + w
          heapq.heappush(minHeap, (dist[v], v))

    return dist
