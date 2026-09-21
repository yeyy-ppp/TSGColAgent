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
  def countServers(self, grid: List[List[int]]) -> int:
    m = len(grid)
    n = len(grid[0])
    ans = 0
    rows = [0] * m
    cols = [0] * n

    for i in range(m):
      for j in range(n):
        if grid[i][j] == 1:
          rows[i] += 1
          cols[j] += 1

    for i in range(m):
      for j in range(n):
        if grid[i][j] == 1 and (rows[i] > 1 or cols[j] > 1):
          ans += 1

    return ans
