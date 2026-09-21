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
  def alertNames(self, keyName: List[str], keyTime: List[str]) -> List[str]:
    nameToMinutes = collections.defaultdict(list)

    for name, time in zip(keyName, keyTime):
      minutes = self._getMinutes(time)
      nameToMinutes[name].append(minutes)

    res=[]
    for name, minutes in nameToMinutes.items():
      if self._hasAlert(minutes):
        res.append(name)
    return sorted(res)

  def _hasAlert(self, minutes: List[int]) -> bool:
    if len(minutes) > 70:
      return True
    minutes.sort()
    for i in range(2, len(minutes)):
      if minutes[i - 2] + 60 >= minutes[i]:
        return True
    return False

  def _getMinutes(self, time: str) -> int:
    h, m = map(int, time.split(':'))
    return 60 * h + m
