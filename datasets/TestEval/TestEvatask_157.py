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
  def mostProfitablePath(self, edges: List[List[int]], bob: int, amount: List[int]) -> int:
    n = len(amount)
    tree = [[] for _ in range(n)]
    parent = [0] * n
    aliceDist = [-1] * n

    for u, v in edges:
      tree[u].append(v)
      tree[v].append(u)

    def dfs(u: int, prev: int, d: int) -> None:
      parent[u] = prev
      aliceDist[u] = d
      for v in tree[u]:
        if aliceDist[v] == -1:
          dfs(v, u, d + 1)

    dfs(0, -1, 0)

    u = bob
    bobDist = 0
    while u != 0:
      if bobDist < aliceDist[u]:
        amount[u] = 0
      elif bobDist == aliceDist[u]:
        amount[u] //= 2
      u = parent[u]
      bobDist += 1

    return self._getMoney(tree, 0, -1, amount)

  def _getMoney(self, tree: List[List[int]], u: int, prev: int, amount: List[int]) -> int:
    if len(tree[u]) == 1 and tree[u][0] == prev:
      return amount[u]

    maxPath = -math.inf
    for v in tree[u]:
      if v != prev:
        maxPath = max(maxPath, self._getMoney(tree, v, u, amount))

    return amount[u] + maxPath
