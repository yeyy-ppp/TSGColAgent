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
  def strongPasswordCheckerII(self, password: str) -> bool:
    if len(password) < 8:
      return False
    if not any(c.islower() for c in password):
      return False
    if not any(c.isupper() for c in password):
      return False
    if not any(c.isdigit() for c in password):
      return False
    if not any("!@#$%^&*()-+".find(c) != -1 for c in password):
      return False
    return all(a != b for a, b in zip(password, password[1:]))
