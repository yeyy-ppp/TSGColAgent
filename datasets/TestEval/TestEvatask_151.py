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
  def latestTimeCatchTheBus(self, buses: List[int], passengers: List[int], capacity: int) -> int:
    buses.sort()
    passengers.sort()

    if passengers[0] > buses[-1]:
      return buses[-1]

    ans = passengers[0] - 1
    i = 0
    j = 0
    while i < len(buses):
      arrived = 0
      while arrived < capacity and j < len(passengers) and passengers[j] <= buses[i]:
        if j > 0 and passengers[j] != passengers[j - 1] + 1:
          ans = passengers[j] - 1
        j += 1
        arrived += 1

      if arrived < capacity and j > 0 and passengers[j - 1] != buses[i]:
        ans = buses[i]
      i += 1

    return ans
