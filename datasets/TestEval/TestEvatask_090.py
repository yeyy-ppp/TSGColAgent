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
  def unhappyFriends(self, n: int, preferences: List[List[int]], pairs: List[List[int]]) -> int:
    ans = 0
    matches = [0] * n
    prefer = [{} for _ in range(n)]

    for x, y in pairs:
      matches[x] = y
      matches[y] = x

    for i in range(n):
      for j in range(n - 1):
        prefer[i][preferences[i][j]] = j

    for x in range(n):
      for u in prefer[x].keys():
        y = matches[x]
        v = matches[u]
        if prefer[x][u] < prefer[x][y] and prefer[u][x] < prefer[u][v]:
          ans += 1
          break

    return ans
