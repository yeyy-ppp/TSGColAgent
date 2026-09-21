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
  def minOperationsQueries(self, n: int, edges: List[List[int]], queries: List[List[int]]) -> List[int]:
    kMax = 26
    m = int(math.log2(n)) + 1
    ans = []
    graph = [[] for _ in range(n)]
    jump = [[0] * m for _ in range(n)]
    count = [[] for _ in range(n)]
    depth = [0] * n

    for u, v, w in edges:
      graph[u].append((v, w))
      graph[v].append((u, w))

    def dfs(u: int, prev: int, d: int):
      if prev != -1:
        jump[u][0] = prev
      depth[u] = d
      for v, w in graph[u]:
        if v == prev:
          continue
        count[v] = count[u][:]
        count[v][w] += 1
        dfs(v, u, d + 1)

    count[0] = [0] * (kMax + 1)
    dfs(0, -1, 0)

    for j in range(1, m):
      for i in range(n):
        jump[i][j] = jump[jump[i][j - 1]][j - 1]

    def getLCA(u: int, v: int) -> int:
      if depth[u] > depth[v]:
        return getLCA(v, u)
      for j in range(m):
        if depth[v] - depth[u] >> j & 1:
          v = jump[v][j]
      if u == v:
        return u
      for j in range(m - 1, -1, -1):
        if jump[u][j] != jump[v][j]:
          u = jump[u][j]
          v = jump[v][j]
      return jump[v][0]

    for u, v in queries:
      lca = getLCA(u, v)
      numEdges = depth[u] + depth[v] - 2 * depth[lca]
      maxFreq = max(count[u][j] + count[v][j] - 2 * count[lca][j] for j in range(1, kMax + 1))
      ans.append(numEdges - maxFreq)

    return ans
