import pandas as pd

class Terminal:
    def __init__(self, latitude, longitude, region):
        self.loc = (latitude, longitude)
        self.region = region

    def __str__(self):
        return f"loc: ({self.loc[0]}, {self.loc[1]}), region: {self.region}"


class Terminal_Table:
    def __init__(self, file_dir=None, graph=None):
        # self.table = {}
        self.graph = graph

        with open(file_dir, 'r', encoding='utf-8') as fs:
            idx = 0
            for line in fs:
                id, latitude, longitude, region = line.split()

                idx = graph.id2idx(id)
                self.graph.coordinates[idx] = (float(latitude), float(longitude))

                """                
                if idx not in self.table:
                    # self.table[idx] = Terminal(latitude, longitude, region)
                    
                else:
                    print("duplicates in terminals.csv")
                    exit(1)
                """