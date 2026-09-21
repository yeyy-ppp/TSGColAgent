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
  def lexicographicallySmallestArray(self, nums: List[int], limit: int) -> List[int]:
    ans = [0] * len(nums)
    numAndIndexes = sorted([(num, i) for i, num in enumerate(nums)])
    numAndIndexesGroups: List[List[Tuple[int, int]]] = []

    for numAndIndex in numAndIndexes:
      if not numAndIndexesGroups or numAndIndex[0] - numAndIndexesGroups[-1][-1][0] > limit:
        numAndIndexesGroups.append([numAndIndex])
      else:
        numAndIndexesGroups[-1].append(numAndIndex)

    for numAndIndexesGroup in numAndIndexesGroups:
      sortedNums = [num for num, _ in numAndIndexesGroup]
      sortedIndices = sorted([index for _, index in numAndIndexesGroup])
      for num, index in zip(sortedNums, sortedIndices):
        ans[index] = num

    return ans
