import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator, Union

class UnionFind:
  def __init__(self, n: int):
    self.id = list(range(n))
    self.rank = [0] * n

  def unionByRank(self, u: int, v: int) -> None:
    i = self.find(u)
    j = self.find(v)
    if i == j:
      return
    if self.rank[i] < self.rank[j]:
      self.id[i] = j
    elif self.rank[i] > self.rank[j]:
      self.id[j] = i
    else:
      self.id[i] = j
      self.rank[j] += 1

  def find(self, u: int) -> int:
    if self.id[u] != u:
      self.id[u] = self.find(self.id[u])
    return self.id[u]


class Solution:
  def findCriticalAndPseudoCriticalEdges(self, n: int, edges: List[List[int]]) -> List[List[int]]:
    criticalEdges = []
    pseudoCriticalEdges = []

    for i in range(len(edges)):
      edges[i].append(i)

    edges.sort(key=lambda x: x[2])

    def getMSTWeight(firstEdge: List[int], deletedEdgeIndex: int) -> Union[int, float]:
      mstWeight = 0
      uf = UnionFind(n)

      if firstEdge:
        uf.unionByRank(firstEdge[0], firstEdge[1])
        mstWeight += firstEdge[2]

      for u, v, weight, index in edges:
        if index == deletedEdgeIndex:
          continue
        if uf.find(u) == uf.find(v):
          continue
        uf.unionByRank(u, v)
        mstWeight += weight

      root = uf.find(0)
      if any(uf.find(i) != root for i in range(n)):
        return math.inf

      return mstWeight

    mstWeight = getMSTWeight([], -1)

    for edge in edges:
      index = edge[3]
      if getMSTWeight([], index) > mstWeight:
        criticalEdges.append(index)
      elif getMSTWeight(edge, -1) == mstWeight:
        pseudoCriticalEdges.append(index)

    return [criticalEdges, pseudoCriticalEdges]
