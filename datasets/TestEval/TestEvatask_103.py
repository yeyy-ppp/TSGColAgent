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
  def eatenApples(self, apples: List[int], days: List[int]) -> int:
    n = len(apples)
    ans = 0
    minHeap = []

    i = 0
    while i < n or minHeap:
      while minHeap and minHeap[0][0] <= i:
        heapq.heappop(minHeap)
      if i < n and apples[i] > 0:
        heapq.heappush(minHeap, (i + days[i], apples[i]))
      if minHeap:
        rottenDay, numApples = heapq.heappop(minHeap)
        if numApples > 1:
          heapq.heappush(minHeap, (rottenDay, numApples - 1))
        ans += 1
      i += 1

    return ans
