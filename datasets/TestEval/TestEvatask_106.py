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
  def maximumGain(self, s: str, x: int, y: int) -> int:
    if x > y:
      return self._gain(s, 'ab', x, 'ba', y)
    else:
      return self._gain(s, 'ba', y, 'ab', x)

  def _gain(self, s: str, sub1: str, point1: int, sub2: str, point2: int) -> int:
    points = 0
    stack1 = []
    stack2 = []

    for c in s:
      if stack1 and stack1[-1] == sub1[0] and c == sub1[1]:
        stack1.pop()
        points += point1
      else:
        stack1.append(c)

    for c in stack1:
      if stack2 and stack2[-1] == sub2[0] and c == sub2[1]:
        stack2.pop()
        points += point2
      else:
        stack2.append(c)

    return points
