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
  def findAllRecipes(self, recipes: List[str], ingredients: List[List[str]], supplies: List[str]) -> List[str]:
    ans = []
    supplies = set(supplies)
    graph = collections.defaultdict(list)
    inDegrees = collections.Counter()
    q = collections.deque()

    for i, recipe in enumerate(recipes):
      for ingredient in ingredients[i]:
        if ingredient not in supplies:
          graph[ingredient].append(recipe)
          inDegrees[recipe] += 1

    for recipe in recipes:
      if inDegrees[recipe] == 0:
        q.append(recipe)

    while q:
      u = q.popleft()
      ans.append(u)
      for v in graph[u]:
        inDegrees[v] -= 1
        if inDegrees[v] == 0:
          q.append(v)

    return ans
