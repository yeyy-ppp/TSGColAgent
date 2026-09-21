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
  def minimumBuckets(self, street: str) -> int:
    A = list(street)

    for i, c in enumerate(A):
      if c == 'H':
        if i > 0 and A[i - 1] == 'B':
          continue
        if i + 1 < len(A) and A[i + 1] == '.':
          A[i + 1] = 'B'
        elif i > 0 and A[i - 1] == '.':
          A[i - 1] = 'B'
        else:
          return -1

    return A.count('B')
