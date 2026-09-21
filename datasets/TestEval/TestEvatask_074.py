import math
import itertools
import bisect
import collections
import string
import heapq
import functools
import sortedcontainers
from typing import List, Dict, Tuple, Iterator
from collections import deque

class Solution:
  def minPushBox(self, grid: List[List[str]]) -> int:
    for i in range(len(grid)):
      for j in range(len(grid[0])):
        if grid[i][j] == "T":
          target = (i,j)
        if grid[i][j] == "B":
          box = (i,j)
        if grid[i][j] == "S":
          person = (i,j)

    def valid(x,y):
      return 0<=x<len(grid) and 0<=y<len(grid[0]) and grid[x][y]!='#'

    def check(curr,dest,box):
      que = deque([curr])
      v = set()
      while que:
        pos = que.popleft()
        if pos == dest: 
          return True
        new_pos = [(pos[0]+1,pos[1]),(pos[0]-1,pos[1]),(pos[0],pos[1]+1),(pos[0],pos[1]-1)]
        for x,y in new_pos:
          if valid(x,y) and (x,y) not in v and (x,y)!=box:
            v.add((x,y))
            que.append((x,y))
      return False

    q = deque([(0,box,person)])
    vis = {box+person}
    while q :
      dist, box, person = q.popleft()
      if box == target:
        return dist

      b_coord = [(box[0]+1,box[1]),(box[0]-1,box[1]),(box[0],box[1]+1),(box[0],box[1]-1)]
      p_coord = [(box[0]-1,box[1]),(box[0]+1,box[1]),(box[0],box[1]-1),(box[0],box[1]+1)]

      for new_box,new_person in zip(b_coord,p_coord): 
        if valid(*new_box) and new_box+box not in vis:
          if valid(*new_person) and check(person,new_person,box):
            vis.add(new_box+box)
            q.append((dist+1,new_box,box))

    return -1
