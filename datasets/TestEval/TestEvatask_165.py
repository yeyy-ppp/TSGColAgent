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
  def collectTheCoins(self, coins: List[int], edges: List[List[int]]) -> int:
    n = len(coins)
    tree = [set() for _ in range(n)]
    leavesToBeRemoved = collections.deque()

    for u, v in edges:
      tree[u].add(v)
      tree[v].add(u)

    for u in range(n):
      while len(tree[u]) == 1 and coins[u] == 0:
        v = tree[u].pop()
        tree[v].remove(u)
        u = v
      if len(tree[u]) == 1:
        leavesToBeRemoved.append(u)

    for _ in range(2):
      for _ in range(len(leavesToBeRemoved)):
        u = leavesToBeRemoved.popleft()
        if tree[u]:
          v = tree[u].pop()
          tree[v].remove(u)
          if len(tree[v]) == 1:
            leavesToBeRemoved.append(v)

    return sum(len(children) for children in tree)
