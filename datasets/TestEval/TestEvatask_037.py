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
  def removeComments(self, source: List[str]) -> List[str]:
    ans = []
    commenting = False
    modified = ''

    for line in source:
      i = 0
      while i < len(line):
        if i + 1 == len(line):
          if not commenting:
            modified += line[i]
          i += 1
          break
        twoChars = line[i:i + 2]
        if twoChars == '/*' and not commenting:
          commenting = True
          i += 2
        elif twoChars == '*/' and commenting:
          commenting = False
          i += 2
        elif twoChars == '//':
          if not commenting:
            break
          else:
            i += 2
        else:
          if not commenting:
            modified += line[i]
          i += 1
      if modified and not commenting:
        ans.append(modified)
        modified = ''

    return ans
