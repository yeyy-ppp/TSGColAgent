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
  def countCompleteSubstrings(self, word: str, k: int) -> int:
    uniqueLetters = len(set(word))
    return sum(self._countCompleteStrings(word, k, windowSize) for windowSize in range(k, k * uniqueLetters + 1, k))

  def _countCompleteStrings(self, word: str, k: int, windowSize: int) -> int:
    res = 0
    countLetters = 0
    count = collections.Counter()

    for i, c in enumerate(word):
      count[c] += 1
      countLetters += 1
      if i > 0 and abs(ord(c) - ord(word[i - 1])) > 2:
        count = collections.Counter()
        count[c] += 1
        countLetters = 1
      if countLetters == windowSize + 1:
        count[word[i - windowSize]] -= 1
        countLetters -= 1
      if countLetters == windowSize:
        res += all(freq == 0 or freq == k for freq in count.values())

    return res
