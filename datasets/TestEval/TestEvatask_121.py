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
  def minCost(self, maxTime: int, edges: List[List[int]], passingFees: List[int]) -> int:
    n = len(passingFees)
    graph = [[] for _ in range(n)]

    for u, v, w in edges:
      graph[u].append((v, w))
      graph[v].append((u, w))

    return self._dijkstra(graph, 0, n - 1, maxTime, passingFees)

  def _dijkstra(self, graph: List[List[Tuple[int, int]]], src: int, dst: int, maxTime: int, passingFees: List[int]) -> int:
    cost = [math.inf for _ in range(len(graph))]
    dist = [maxTime + 1 for _ in range(len(graph))]

    cost[src] = passingFees[src]
    dist[src] = 0
    minHeap = [(cost[src], dist[src], src)]

    while minHeap:
      currCost, d, u = heapq.heappop(minHeap)
      if u == dst:
        return cost[dst]
      if d > dist[u] and currCost > cost[u]:
        continue
      for v, w in graph[u]:
        if d + w > maxTime:
          continue
        if currCost + passingFees[v] < cost[v]:
          cost[v] = currCost + passingFees[v]
          dist[v] = d + w
          heapq.heappush(minHeap, (cost[v], dist[v], v))
        elif d + w < dist[v]:
          dist[v] = d + w
          heapq.heappush(minHeap, (currCost + passingFees[v], dist[v], v))

    return -1
