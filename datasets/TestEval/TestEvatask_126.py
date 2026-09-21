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
  def numberOfGoodSubsets(self, nums: List[int]) -> int:
    kMod = 1_000_000_007
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    n = 1 << len(primes)
    dp = [1] + [0] * (n - 1)
    count = collections.Counter(nums)

    for num, freq in count.items():
      if num == 1:
        continue
      if any(num % squared == 0 for squared in [4, 9, 25]):
        continue
      numPrimesMask = 0
      for i, prime in enumerate(primes):
        if num % prime == 0:
          numPrimesMask += 1 << i
      for primesMask in range(n):
        if primesMask & numPrimesMask > 0:
          continue
        nextPrimesMask = numPrimesMask | primesMask
        dp[nextPrimesMask] += dp[primesMask] * freq
        dp[nextPrimesMask] %= kMod

    return (1 << count[1]) * sum(dp[1:]) % kMod
