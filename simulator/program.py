import copy
import os
import time

import config
from object.graph import Graph
from object.order import OrderTable
from object.terminal import Terminal_Table
from object.vehicle import Vehicle_Table
from tool.tools import *
from solution.init_solution.initial_solution_generator import Initial_Solution_Generator
from solution.solver.solver import Solver


class Program:
    def __init__(self):
        self.start_time = time.time()
        config.TIMEOUT = self.start_time + config.TIME_CONSTRAINT

        self.graph = Graph(config.OD_MATRIX)
        print("Graph constructed")
        self.vehicleTable = Vehicle_Table(config.VEHICLES, self.graph)
        print("Vehicle Table constructed")
        self.terminalTable = Terminal_Table(config.TERMINALS, self.graph)
        print("Terminal Table constructed")
        self.orderTable = OrderTable(config.ORDERS, self.graph)
        print("Order Table constructed", end="\n\n")
        self.graph.write_coordinates()

    def simulator(self):
        print("Simulation ongoing..")

        left = []
        for group in range(config.LAST_BATCH):
            result_dir = os.path.join("results", f"order_result{group}.csv")

            # left
            batch = copy.copy(self.orderTable.table[group])
            if len(batch)==0: continue
            batch.extend(left)

            # free_time update
            self.vehicleTable.update_freetime(group * config.GROUP_INTERVAL)

            # init solution
            print(f"\nbatch {group} : ")
            init_solution_generator = Initial_Solution_Generator(
                graph = self.graph,
                vehicle_list= self.vehicleTable.table,
                order_list= batch,
                carry_over = ((group+1)!=config.LAST_BATCH),
                group = group
            )
            init_solution = init_solution_generator.get_init_solution()

            # optimization
            solution = init_solution
            solver = Solver(solution, self.graph, group)
            solution = solver.solve()

            # allocation
            print(f"\t{solution}", end=' ')
            solution.update()
            solution.allocate_solution()
            self.vehicleTable.update_allocated_orders(group * config.GROUP_INTERVAL)
            self.vehicleTable.write_order_result(os.path.join("results", f"order_result{group}.csv"))

            left = []
            for order in batch:
                ## 72 hour limit
                if order.serviced: continue
                left.append(order)

            with open(result_dir, 'a') as f:
                for order in left: f.write(str(order) + '\n')

            print(f"{len(batch)} -> {len(left)}")
            print(f"\tTotal Cost: {self.vehicleTable.get_total_cost():.2f}")

        self.vehicleTable.update_allocated_orders(config.WEEK)
        self.vehicleTable.write_order_result(config.FINAL_ORDER_RESULT_DIR)
        self.vehicleTable.write_veh_result()

        print(self.orderTable)
        print(f"Final Cost: {self.vehicleTable.get_total_cost():.2f}")





