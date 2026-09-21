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
  def smallestBeautifulString(self, s: str, k: int) -> str:
    chars = list(s)

    for i in reversed(range(len(chars))):
      chars[i] = chr(ord(chars[i]) + 1)
      while self._containsPalindrome(chars, i):
        chars[i] = chr(ord(chars[i]) + 1)
      if chars[i] < chr(ord('a') + k):
        return self._changeSuffix(chars, i + 1)

    return ''

  def _containsPalindrome(self, chars: List[str], i: int) -> bool:
    return (i > 0 and chars[i] == chars[i - 1]) or (i > 1 and chars[i] == chars[i - 2])

  def _changeSuffix(self, chars: List[str], i: int) -> str:
    for j in range(i, len(chars)):
      chars[j] = 'a'
      while self._containsPalindrome(chars, j):
        chars[j] = chr(ord(chars[j]) + 1)
    return ''.join(chars)
