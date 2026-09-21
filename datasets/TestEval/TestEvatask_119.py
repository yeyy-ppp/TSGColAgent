import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator, Set

class Solution:
  def __init__(self):
    self.kMod = 8_417_508_174_513
    self.kBase = 165_131

  def longestCommonSubpath(self, n: int, paths: List[List[int]]) -> int:
    l = 0
    r = len(paths[0])

    while l < r:
      m = l + (r - l + 1) // 2
      if self._checkCommonSubpath(paths, m):
        l = m
      else:
        r = m - 1

    return l

  def _checkCommonSubpath(self, paths: List[List[int]], m: int) -> bool:
    hashSets = [self._rabinKarp(path, m) for path in paths]

    for subpathHash in hashSets[0]:
      if all(subpathHash in hashSet for hashSet in hashSets):
        return True

    return False

  def _rabinKarp(self, path: List[int], m: int) -> Set[int]:
    hashes = set()
    maxPower = 1
    hash = 0

    for i, num in enumerate(path):
      hash = (hash * self.kBase + num) % self.kMod
      if i >= m:
        hash = (hash - path[i - m] * maxPower % self.kMod + self.kMod) % self.kMod
      else:
        maxPower = maxPower * self.kBase % self.kMod
      if i >= m - 1:
        hashes.add(hash)

    return hashes
