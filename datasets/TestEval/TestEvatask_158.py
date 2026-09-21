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
  def minimumTotalCost(self, nums1: List[int], nums2: List[int]) -> int:
    n = len(nums1)
    ans = 0
    maxFreq = 0
    maxFreqNum = 0
    shouldBeSwapped = 0
    conflictedNumCount = [0] * (n + 1)

    for i, (num1, num2) in enumerate(zip(nums1, nums2)):
      if num1 == num2:
        conflictedNum = num1
        conflictedNumCount[conflictedNum] += 1
        if conflictedNumCount[conflictedNum] > maxFreq:
          maxFreq = conflictedNumCount[conflictedNum]
          maxFreqNum = conflictedNum
        shouldBeSwapped += 1
        ans += i

    for i, (num1, num2) in enumerate(zip(nums1, nums2)):
      if maxFreq * 2 <= shouldBeSwapped:
        break
      if num1 == num2:
        continue

      if num1 == maxFreqNum or num2 == maxFreqNum:
        continue
      shouldBeSwapped += 1
      ans += i

    if maxFreq * 2 > shouldBeSwapped:
      return -1
    else:
      return ans
