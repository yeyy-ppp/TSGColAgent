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
  def countPairs(self, n: int, edges: List[List[int]], queries: List[int]) -> List[int]:
    ans = [0] * len(queries)

    count = [0] * (n + 1)

    shared = [collections.Counter() for _ in range(n + 1)]

    for u, v in edges:
      count[u] += 1
      count[v] += 1
      shared[min(u, v)][max(u, v)] += 1

    sortedCount = sorted(count)

    for k, query in enumerate(queries):
      i = 1
      j = n
      while i < j:
        if sortedCount[i] + sortedCount[j] > query:
          ans[k] += j - i
          j -= 1
        else:
          i += 1
      for i in range(1, n + 1):
        for j, sh in shared[i].items():
          if count[i] + count[j] > query and count[i] + count[j] - sh <= query:
            ans[k] -= 1

    return ans
