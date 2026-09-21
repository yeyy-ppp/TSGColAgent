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
  def primePalindrome(self, n: int) -> int:
    def getPalindromes(n: int):
      length = n // 2
      for i in range(10**(length - 1), 10**length):
        s = str(i)
        for j in range(10):
          yield int(s + str(j) + s[::-1])

    def isPrime(num: int) -> bool:
      for i in range(2, int(num**0.5 + 1)):
        if num % i == 0:
          return False
      return True

    if n <= 2:
      return 2
    if n == 3:
      return 3
    if n <= 5:
      return 5
    if n <= 7:
      return 7
    if n <= 11:
      return 11

    nLength = len(str(n))

    while True:
      for num in getPalindromes(nLength):
        if num >= n and isPrime(num):
          return num
      nLength += 1
