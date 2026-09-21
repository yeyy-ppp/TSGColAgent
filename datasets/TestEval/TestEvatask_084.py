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
  def checkIfPrerequisite(self, numCourses: int, prerequisites: List[List[int]], queries: List[List[int]]) -> List[bool]:
    graph = [[] for _ in range(numCourses)]
    isPrerequisite = [[False] * numCourses for _ in range(numCourses)]

    for u, v in prerequisites:
      graph[u].append(v)

    for i in range(numCourses):
      self._dfs(graph, i, isPrerequisite[i])

    return [isPrerequisite[u][v] for u, v in queries]

  def _dfs(self, graph: List[List[int]], u: int, used: List[bool]) -> None:
    for v in graph[u]:
      if used[v]:
        continue
      used[v] = True
      self._dfs(graph, v, used)
