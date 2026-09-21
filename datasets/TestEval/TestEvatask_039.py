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
  def asteroidCollision(self, asteroids: List[int]) -> List[int]:
    stack = []

    for a in asteroids:
      if a > 0:
        stack.append(a)
      else:
        while stack and stack[-1] > 0 and stack[-1] < -a:
          stack.pop()
        if not stack or stack[-1] < 0:
          stack.append(a)
        elif stack[-1] == -a:
          stack.pop()
        else:
          pass

    return stack
