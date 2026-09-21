import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator

from enum import Enum


class Direction(Enum):
  kForward = 0
  kBackward = 1


class Solution:
  def minimumJumps(self, forbidden: List[int], a: int, b: int, x: int) -> int:
    furthest = max(x + a + b, max(pos + a + b for pos in forbidden))
    seenForward = {pos for pos in forbidden}
    seenBackward = {pos for pos in forbidden}

    q = collections.deque([(Direction.kForward, 0)])

    ans = 0
    while q:
      for _ in range(len(q)):
        dir, pos = q.popleft()
        if pos == x:
          return ans
        forward = pos + a
        backward = pos - b
        if forward <= furthest and forward not in seenForward:
          seenForward.add(forward)
          q.append((Direction.kForward, forward))
        if dir == Direction.kForward and backward >= 0 and backward not in seenBackward:
          seenBackward.add(backward)
          q.append((Direction.kBackward, backward))
      ans += 1

    return -1
