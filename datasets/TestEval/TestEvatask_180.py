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
  def getMaxFunctionValue(self, receiver: List[int], k: int) -> int:
    n = len(receiver)
    m = int(math.log2(k)) + 1
    ans = 0
    jump = [[0] * m for _ in range(n)]
    summ = [[0] * m for _ in range(n)]

    for i in range(n):
      jump[i][0] = receiver[i]
      summ[i][0] = receiver[i]

    for j in range(1, m):
      for i in range(n):
        midNode = jump[i][j - 1]
        jump[i][j] = jump[midNode][j - 1]
        summ[i][j] = summ[i][j - 1] + summ[midNode][j - 1]

    for i in range(n):
      currSum = i
      currPos = i
      for j in range(m):
        if (k >> j) & 1 == 1:
          currSum += summ[currPos][j]
          currPos = jump[currPos][j]
      ans = max(ans, currSum)

    return ans
