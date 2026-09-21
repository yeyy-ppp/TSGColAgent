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
  def reformat(self, s: str) -> str:
    A=[]
    for c in s:
      if c.isalpha():
        A.append(c)
    B=[]
    for c in s:
      if c.isdigit():
        B.append(c)

    if len(A) < len(B):
      A, B = B, A
    if len(A) - len(B) > 1:
      return ''

    ans = []

    for i in range(len(B)):
      ans.append(A[i])
      ans.append(B[i])

    if len(A) == len(B) + 1:
      ans.append(A[-1])
    return ''.join(ans)
