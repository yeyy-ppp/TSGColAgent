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
  def largest1BorderedSquare(self, grid: List[List[int]]) -> int:
    m = len(grid)
    n = len(grid[0])

    leftOnes = [[0] * n for _ in range(m)]
    topOnes = [[0] * n for _ in range(m)]

    for i in range(m):
      for j in range(n):
        if grid[i][j] == 1:
          if j==0:
            leftOnes[i][j]=1
          else:
            leftOnes[i][j]=1+leftOnes[i][j-1]
          if i==0:
            topOnes[i][j]=1
          else:
            topOnes[i][j]=1+topOnes[i-1][j]

    for sz in range(min(m, n), 0, -1):
      for i in range(m - sz + 1):
        for j in range(n - sz + 1):
          x = i + sz - 1
          y = j + sz - 1
          if min(leftOnes[i][y], leftOnes[x][y], topOnes[x][j], topOnes[x][y]) >= sz:
            return sz * sz

    return 0
