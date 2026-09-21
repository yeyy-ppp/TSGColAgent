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
  def checkWays(self, pairs: List[List[int]]) -> int:
    kMax = 501
    graph = collections.defaultdict(list)
    degrees = [0] * kMax
    connected = [[False] * kMax for _ in range(kMax)]

    for u, v in pairs:
      graph[u].append(v)
      graph[v].append(u)
      degrees[u] += 1
      degrees[v] += 1
      connected[u][v] = True
      connected[v][u] = True

    for _, children in graph.items():
      children.sort(key=lambda a: degrees[a], reverse=True)

    root = next((i for i, d in enumerate(degrees) if d == len(graph) - 1), -1)
    if root == -1:
      return 0

    hasMoreThanOneWay = False

    def dfs(u: int, ancestors: List[int], seen: List[bool]) -> bool:
      nonlocal hasMoreThanOneWay
      seen[u] = True
      for ancestor in ancestors:
        if not connected[u][ancestor]:
          return False
      ancestors.append(u)
      for v in graph[u]:
        if seen[v]:
          continue
        if degrees[v] == degrees[u]:
          hasMoreThanOneWay = True
        if not dfs(v, ancestors, seen):
          return False
      ancestors.pop()
      return True

    if not dfs(root, [], [False] * kMax):
      return 0
    if hasMoreThanOneWay:
      return 2
    else:
      return 1
