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
  def boxDelivering(self, boxes: List[List[int]], portsCount: int, maxBoxes: int, maxWeight: int) -> int:
    n = len(boxes)
    dp = [0] * (n + 1)
    trips = 2
    weight = 0

    l = 0
    for r in range(n):
      weight += boxes[r][1]

      if r > 0 and boxes[r][0] != boxes[r - 1][0]:
        trips += 1

      while r - l + 1 > maxBoxes or weight > maxWeight or (l < r and dp[l + 1] == dp[l]):
        weight -= boxes[l][1]
        if boxes[l][0] != boxes[l + 1][0]:
          trips -= 1
        l += 1

      dp[r + 1] = dp[l] + trips

    return dp[n]
