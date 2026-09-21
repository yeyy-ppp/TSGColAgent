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
  def secondMinimum(self, n: int, edges: List[List[int]], time: int, change: int) -> int:
    graph = [[] for _ in range(n + 1)]
    q = collections.deque([(1, 0)])
    minTime = [[math.inf] * 2 for _ in range(n + 1)]
    minTime[1][0] = 0

    for u, v in edges:
      graph[u].append(v)
      graph[v].append(u)

    while q:
      i, prevTime = q.popleft()

      numChangeSignal = prevTime // change
      waitTime = change - (prevTime % change) if numChangeSignal & 1 else 0
      newTime = prevTime + waitTime + time
      for j in graph[i]:
        if newTime < minTime[j][0]:
          minTime[j][0] = newTime
          q.append((j, newTime))
        elif minTime[j][0] < newTime < minTime[j][1]:
          if j == n:
            return newTime
          minTime[j][1] = newTime
          q.append((j, newTime))
