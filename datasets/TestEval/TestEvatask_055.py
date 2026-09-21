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
  def snakesAndLadders(self, board: List[List[int]]) -> int:
    n = len(board)
    ans = 0
    q = collections.deque([1])
    seen = set()
    A = [0] * (1 + n * n)

    for i in range(n):
      for j in range(n):
        if n - i & 1 :
          A[(n - 1 - i) * n + (j + 1)] = board[i][j]
        else:
          A[(n - 1 - i) * n + (n - j)] = board[i][j]

    while q:
      ans += 1
      for _ in range(len(q)):
        curr = q.popleft()
        for next in range(curr + 1, min(curr + 6, n * n) + 1):
          dest = A[next] if A[next] > 0 else next
          if dest == n * n:
            return ans
          if dest in seen:
            continue
          q.append(dest)
          seen.add(dest)

    return -1
