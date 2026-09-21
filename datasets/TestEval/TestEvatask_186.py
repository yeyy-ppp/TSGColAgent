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
  def getWordsInLongestSubsequence(self, words: List[str], groups: List[int]) -> List[str]:
    ans = []
    n=len(words)
    dp = [1] * n
    prev = [-1] * n

    for i in range(1, n):
      for j in range(i):
        if groups[i] == groups[j]:
          continue
        if len(words[i]) != len(words[j]):
          continue
        if sum(a != b for a, b in zip(words[i], words[j])) != 1:
          continue
        if dp[i] < dp[j] + 1:
          dp[i] = dp[j] + 1
          prev[i] = j

    index = dp.index(max(dp))
    while index != -1:
      ans.append(words[index])
      index = prev[index]

    return ans[::-1]
