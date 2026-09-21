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
  def numberOfCombinations(self, num: str) -> int:
    if num[0] == '0':
      return 0

    kMod = 1_000_000_007
    n = len(num)
    dp = [[0] * (n + 1) for _ in range(n)]
    lcs = [[0] * (n + 1) for _ in range(n + 1)]

    for i in range(n - 1, -1, -1):
      for j in range(i + 1, n):
        if num[i] == num[j]:
          lcs[i][j] = lcs[i + 1][j + 1] + 1

    for i in range(n):
      for k in range(1, i + 2):
        dp[i][k] += dp[i][k - 1]
        dp[i][k] %= kMod
        s = i - k + 1
        if num[s] == '0':
          continue
        if s == 0:
          dp[i][k] += 1
          continue
        if s < k:
          dp[i][k] += dp[s - 1][s]
          continue
        l = lcs[s - k][s]
        if l >= k or num[s - k + l] <= num[s + l]:
          dp[i][k] += dp[s - 1][k]
        else:
          dp[i][k] += dp[s - 1][k - 1]

    return dp[n - 1][n] % kMod
