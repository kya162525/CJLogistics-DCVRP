import math
from typing import Dict
from collections import defaultdict

import config
from config import *


class edge:
    def __init__(self, time_ = -1, dist_ = -1):
        self.time = time_
        self.dist = dist_


class Graph:
    def __init__(self, file_dir):
        self.table = None
        self.IDX = {}
        self.ID = []
        self.coordinates = [] # ( latitude, longitude )

        # table reset with {-1, -1}
        init_value = edge()
        self.table = [[init_value for _ in range(GRAPH_SIZE)] for _ in range(GRAPH_SIZE)]
        self.dist_table = [[0 for _ in range(GRAPH_SIZE)] for _ in range(GRAPH_SIZE)]
        for i in range(GRAPH_SIZE):
            self.table[i][i] = edge(0,0)

        with open(file_dir, 'r') as fs:
            idx = 0
            for line in fs:
                origin, dest, dist, time = line.split()
                # index setting
                if origin not in self.IDX:
                    self.IDX[origin] = idx
                    self.ID.append(origin)
                    idx += 1
                if dest not in self.IDX:
                    self.IDX[dest] = idx
                    self.ID.append(dest)
                    idx += 1
                from_, to_ = self.IDX[origin], self.IDX[dest]

                time = float(time)
                dist = float(dist)

                # adj matrix
                self.table[from_][to_] = edge(time, dist)

        self.coordinates= [(-1.0,-1.0) for _ in range(idx)]
        if idx!= len(self.ID):
            print("graph not complete")
            exit(1)

        # WRITE IDX2ID
        with open(IDX2ID_DIR, 'w') as f:
            f.write("IDX,ID\n")
            for idx, id in enumerate(self.ID):
                f.write(f"{idx},{id}\n")

    def is_terminal(self, idx:int):
        return self.ID[idx].startswith(TERMINAL_START_CHARACTER)

    def get_time(self, from_, to_, cost=False):
        ret = self.table[from_][to_].time
        if cost: return ret
        return int(math.ceil(ret)) if INTEGER else ret

    def get_dist(self, from_, to_, cost=False):
        ret = self.table[from_][to_].dist
        if cost: return ret
        return int(math.ceil(ret)) if INTEGER else ret

    def get_size(self):
        return len(self.ID)

    def id2idx(self, id):
        if id not in self.IDX:
            print(id, "is not in od_matrix")
            exit(1)
        return self.IDX[id]

    def idx2id(self, idx):
        if idx >= len(self.ID) or idx < 0:
            print(idx, "is not a valid index.")
            exit(1)
        return self.ID[idx]

    def get_coordinates(self, idx:int):
        return self.coordinates[idx]

    def write_coordinates(self):

        with open(config.COORDINAES_DIR, 'w') as f:
            f.write("idx,latitude,longitude\n")
            for idx, coordinates in enumerate(self.coordinates):
                f.write(f"{str(idx)},{str(coordinates[0])},{str(coordinates[1])}\n")




