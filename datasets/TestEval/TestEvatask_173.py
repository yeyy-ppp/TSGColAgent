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
  def maxStrength(self, nums: List[int]) -> int:
    posProd = 1
    negProd = 1
    maxNeg = -math.inf
    negCount = 0
    hasPos = False
    hasZero = False

    for num in nums:
      if num > 0:
        posProd *= num
        hasPos = True
      elif num < 0:
        negProd *= num
        maxNeg = max(maxNeg, num)
        negCount += 1
      else:
        hasZero = True

    if negCount == 0 and not hasPos:
      return 0
    if negCount % 2 == 0:
      return negProd * posProd
    if negCount >= 3:
      return negProd // maxNeg * posProd
    if hasPos:
      return posProd
    if hasZero:
      return 0
    return maxNeg
