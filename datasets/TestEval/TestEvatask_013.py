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
  def gameOfLife(self, board: List[List[int]]) -> None:
    m = len(board)
    n = len(board[0])

    for i in range(m):
      for j in range(n):
        ones = 0
        for x in range(max(0, i - 1), min(m, i + 2)):
          for y in range(max(0, j - 1), min(n, j + 2)):
            ones += board[x][y] & 1

        if board[i][j] == 1 and (ones == 3 or ones == 4):
          board[i][j] |= 0b10

        if board[i][j] == 0 and ones == 3:
          board[i][j] |= 0b10

    for i in range(m):
      for j in range(n):
        board[i][j] >>= 1
