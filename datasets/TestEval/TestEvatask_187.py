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
  def shortestBeautifulSubstring(self, s: str, k: int) -> str:
    bestLeft = -1
    minLength = len(s) + 1
    ones = 0

    l = 0
    for r, c in enumerate(s):
      if c == '1':
        ones += 1
      while ones == k:
        if r - l + 1 < minLength:
          bestLeft = l
          minLength = r - l + 1
        elif r - l + 1 == minLength and s[l:l + minLength] < s[bestLeft:bestLeft + minLength]:
          bestLeft = l
        if s[l] == '1':
          ones -= 1
        l += 1

    if bestLeft == -1:
      return ""
    else:
      return s[bestLeft:bestLeft + minLength]
