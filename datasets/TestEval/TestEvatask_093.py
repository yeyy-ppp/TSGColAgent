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
  def maximalNetworkRank(self, n: int, roads: List[List[int]]) -> int:
    degrees = [0] * n

    for u, v in roads:
      degrees[u] += 1
      degrees[v] += 1

    maxDegree1 = 0
    maxDegree2 = 0
    for degree in degrees:
      if degree > maxDegree1:
        maxDegree2 = maxDegree1
        maxDegree1 = degree
      elif degree > maxDegree2:
        maxDegree2 = degree

    countMaxDegree1 = 0
    countMaxDegree2 = 0
    for degree in degrees:
      if degree == maxDegree1:
        countMaxDegree1 += 1
      elif degree == maxDegree2:
        countMaxDegree2 += 1

    if countMaxDegree1 == 1:
      edgeCount = self._getEdgeCount(roads, degrees, maxDegree1, maxDegree2) + self._getEdgeCount(roads, degrees, maxDegree2, maxDegree1)
      return maxDegree1 + maxDegree2 - (countMaxDegree2 == edgeCount)
    else:
      edgeCount = self._getEdgeCount(roads, degrees, maxDegree1, maxDegree1)
      maxPossibleEdgeCount = countMaxDegree1 * (countMaxDegree1 - 1) // 2
      return 2 * maxDegree1 - (maxPossibleEdgeCount == edgeCount)

  def _getEdgeCount(self, roads: List[List[int]], degrees: List[int], degreeU: int, degreeV: int) -> int:
    edgeCount = 0
    for u, v in roads:
      if degrees[u] == degreeU and degrees[v] == degreeV:
        edgeCount += 1
    return edgeCount
