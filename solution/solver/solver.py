import copy
import time
from random import shuffle
import math
import random

import config
from solution.Solution import Solution
from itertools import combinations, combinations_with_replacement
from object.graph import Graph
from solution.vehicle_alloc import Vehicle_Alloc
from tool.tools import deque_slice, list_insert, random_combinations, euclidean_distance, list_delete, time_check, \
    veh_combination, write_solver_result


class Solver:
    def __init__(self, solution: Solution, graph: Graph, cur_batch):
        self.solution = solution
        self.best_solution = copy.copy(solution)
        self.graph = graph
        self.cur_batch = cur_batch
        self.last = ((cur_batch + 1)==config.LAST_BATCH)
        self.start_sec = time.time()
        self.simulated_annealing = False

        if config.DEBUG:
            for dir in config.SOLVER_DIRS:
                with open(dir, 'w') as f:
                    f.write(config.SOLVER_COLUMNS + '\n')

        self.allocated_time = (config.TIMEOUT - self.start_sec) / (config.LAST_BATCH - self.cur_batch)

    def solve(self):

        funs = [
            ("swap vehicles", self.swap_vehicles),
            ("swap orders", self.swap_orders),
            ("swap spatial bundles", self.swap_spatial_bundles),
            ("swap cycles", self.swap_cycles),
            ("distribute cycles", self.distribute_cycles)
        ]

        print(f"\tinit solution -> {self.solution.get_total_cost():.2f}")

        for _ in range(config.NUM_ITER):
            swapped = False
            temp_cost = self.solution.get_total_cost()

            for name, fun in funs:
                cnt = fun()
                swapped |= cnt > 0
                if self.simulated_annealing:
                    print(f"\t{name:17s} \t({cnt}) \t-> {self.solution.get_total_cost():.2f}, {self.best_solution.get_total_cost():.2f}")
                else:
                    print(f"\t{name:17s} \t({cnt}) \t-> {self.solution.get_total_cost():.2f}")

            end_sec = time.time()
            cost_reduction = temp_cost - self.solution.get_total_cost()
            if (end_sec - self.start_sec > self.allocated_time): break
            if not swapped and not config.SIMULATED_ANNEALING: break
            if (0 <= cost_reduction < 1) and self.simulated_annealing: break
            if not self.simulated_annealing and (not swapped or cost_reduction < 1):
                print("\t-- TURN SIMULATED ANNEALING ON --")
                self.best_solution = copy.copy(self.solution)
                self.simulated_annealing = True

        if self.solution.get_total_cost() < self.best_solution.get_total_cost():
            self.best_solution = copy.copy(self.solution)

        return self.best_solution


    def distribute_cycles(self):

        distributed = True
        cnt = 0
        comb = combinations(self.solution.vehicle_list, 2)

        while distributed and cnt < 100:
            distributed = False

            for veh1, veh2 in comb:

                if len(veh1.order_list)>0 and len(veh2.order_list) ==0:
                    if self.distribute_cycle_try(veh1, veh2):
                        distributed = True
                        cnt += 1

        return cnt

    def distribute_cycle_try(self, veh1, veh2) -> bool:

        for idx1 in range(len(veh1.cycle_list)):
            if self.do_distribute_cycle(veh1, idx1, veh2):
                return True
        return False

    def do_distribute_cycle(self, veh1, cycle1_idx, veh2):
        """
        veh1 -> veh2 insertion
        :param veh1:
        :param cycle1_idx:
        :param veh2:
        :param cycle2_idx:
        :return:
        """
        cycle1 = veh1.cycle_list[cycle1_idx]


        # feasibility - cbm
        max1 = 0
        for order in cycle1.orders: max1 = max(order.cbm, max1)
        if max1 > veh2.vehicle.capa: return False

        start_idx1 = 0
        for i in range(cycle1_idx): start_idx1 += veh1.cycle_list[i].get_cycle_order_cnt()
        end_idx1 = start_idx1 + cycle1.get_cycle_order_cnt()


        veh1_temp_list = copy.copy(veh1.order_list)
        veh2_temp_list = copy.copy(veh1.order_list[start_idx1:end_idx1])
        veh1_temp_list = list_delete(veh1_temp_list, start_idx1, end_idx1)

        temp_veh1 = Vehicle_Alloc(veh1.vehicle, self.graph, veh1_temp_list)
        temp_veh2 = Vehicle_Alloc(veh2.vehicle, self.graph, veh2_temp_list)
        temp_veh1.update()
        temp_veh2.update()

        # violation check
        if temp_veh1.get_time_violation() + temp_veh2.get_time_violation() > 0: return False

        # cost check
        original_cost = veh1.get_added_cost() + veh2.get_added_cost()
        new_cost = temp_veh1.get_added_cost() + temp_veh2.get_added_cost()
        if new_cost >= original_cost: return False

        # time check
        time_limit = (self.cur_batch + 1) * config.GROUP_INTERVAL
        if time_check(temp_veh1.order_list, time_limit = time_limit, last = self.last) and \
            time_check(temp_veh2.order_list, time_limit =time_limit, last = self.last ):

            if config.DEBUG:
                write_solver_result(config.DISTRIBUTION_DIR, cost_delta = original_cost-new_cost,
                                route1=veh1.get_route(), route2=veh2.get_route(),
                                new_route1=temp_veh1.get_route(), new_route2=temp_veh2.get_route())

            veh1.order_list = veh1_temp_list
            veh2.order_list = veh2_temp_list
            for veh in [veh1, veh2]: veh.update()

            if self.simulated_annealing and self.solution.get_total_cost() < self.best_solution.get_total_cost():
                self.best_solution = copy.copy(self.solution)

            return True
        else:
            return False


    def swap_vehicles(self):
        swapped = True
        cnt = 0


        while swapped and cnt < 1000:
            swapped= False
            for veh1, veh2 in combinations(self.solution.vehicle_list, 2):
                if self.do_swap_vehicle(veh1, veh2):
                    swapped = True
                    cnt += 1

        return cnt


    def do_swap_vehicle(self, veh1, veh2) -> bool:
        if len(veh1.order_list) + len(veh2.order_list) == 0: return False
        # capa check
        max1 = max2 = 0
        for order in veh1.order_list:
            max1 = max(max1, order.order.cbm)
        for order in veh2.order_list:
            max2 = max(max2, order.order.cbm)
        if max1 > veh2.vehicle.capa: return False
        if max2 > veh1.vehicle.capa: return False

        temp_veh1 = Vehicle_Alloc(veh1.vehicle, self.graph, veh2.order_list)
        temp_veh2 = Vehicle_Alloc(veh2.vehicle, self.graph, veh1.order_list)

        # violation
        if temp_veh1.get_violation() + temp_veh2.get_violation() > 0: return False

        if len(temp_veh1.order_list) > 0:
            order_helper = temp_veh1.order_list[-1]
            start_time = order_helper.departure_time - order_helper.order.load
            if self.last is False and (start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL): return False
            if self.last and (start_time > config.MAX_START_TIME): return False
        if len(temp_veh2.order_list) > 0:
            order_helper = temp_veh2.order_list[-1]
            start_time = order_helper.departure_time - order_helper.order.load
            if self.last is False and (start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL): return False
            if self.last and start_time >= config.MAX_START_TIME: return False

        # cost reduction check
        original_cost = veh1.get_added_cost() + veh2.get_added_cost()
        new_cost = temp_veh1.get_added_cost() + temp_veh2.get_added_cost()
        if new_cost >= original_cost: return False

        # now swap
        if config.DEBUG:
            write_solver_result(config.SWAP_VEHICLE_DIR, cost_delta=original_cost - new_cost,
                                route1=veh1.get_route(), route2=veh2.get_route(),
                                new_route1=temp_veh1.get_route(), new_route2=temp_veh2.get_route(),
                                veh1 = veh1.vehicle.veh_num, veh2= veh2.vehicle.veh_num)

        temp = veh1.order_list
        veh1.order_list = veh2.order_list
        veh2.order_list = temp
        for veh in [veh1, veh2]: veh.update()
        if self.simulated_annealing and self.solution.get_total_cost() < self.best_solution.get_total_cost():
            self.best_solution = copy.copy(self.solution)

        return True

    def swap_spatial_bundles(self):
        swapped = True
        cnt = 0

        comb = combinations(self.solution.vehicle_list, 2)
        while swapped and cnt < 200:
            swapped = False
            for veh1, veh2 in comb:
                if self.spatial_bundle_try(veh1, veh2):
                    cnt += 1
                    swapped = True
        return cnt



    def spatial_bundle_try(self,veh1:Vehicle_Alloc, veh2:Vehicle_Alloc) -> bool:

        for idx1 in range(len(veh1.spatial_bundle)):
            for idx2 in range(len(veh2.spatial_bundle)):

                if euclidean_distance(veh1.spatial_bundle[idx1].center,
                                      veh2.spatial_bundle[idx2].center) > config.SPATIAL_BUNDLE_CRITERION:
                    continue
                if self.do_swap_spatial_bundle(veh1, veh2, idx1, idx2):
                    return True
        return False


    def do_swap_spatial_bundle(self, veh1:Vehicle_Alloc, veh2:Vehicle_Alloc, idx1, idx2) -> bool:
        if len(veh1.order_list)==0 and len(veh2.order_list)==0: return False

        from1 = from2 = 0

        if idx1 != 0:
            for bundle in veh1.spatial_bundle[:idx1-1]: from1 += bundle.get_size()
        if idx2 != 0:
            for bundle in veh2.spatial_bundle[:idx2-1]: from2 += bundle.get_size()
        to1 = from1 + veh1.spatial_bundle[idx1].get_size()
        to2 = from2 + veh2.spatial_bundle[idx2].get_size()

        # feasibility - cbm
        max1 = max2 = 0
        for order in veh1.order_list[from1:to1]:
            max1 = max(order.order.cbm, max1)
        for order in veh2.order_list[from2:to2]:
            max2 = max(order.order.cbm, max2)
        if max1 > veh2.vehicle.capa: return False
        if max2 > veh1.vehicle.capa: return False

        veh1_temp = copy.copy(veh1.order_list)
        veh2_temp = copy.copy(veh2.order_list)
        temp1 = copy.copy(veh1.order_list[from1:to1])
        temp2 = copy.copy(veh2.order_list[from2:to2])
        veh1_temp = list_insert(veh1_temp, from1, to1, temp2)
        veh2_temp = list_insert(veh2_temp, from2, to2, temp1)

        veh1_alloc_temp = Vehicle_Alloc(veh1.vehicle, self.graph, allocated_order_list=veh1_temp)
        veh2_alloc_temp = Vehicle_Alloc(veh2.vehicle, self.graph, allocated_order_list=veh2_temp)

        # violation
        if veh1_alloc_temp.get_violation() + veh2_alloc_temp.get_violation() > 0: return False

        # feasibility - time
        start_time1 = veh1_alloc_temp.order_list[-1].departure_time - veh1_alloc_temp.order_list[-1].order.load
        if self.last is False and start_time1 > (self.cur_batch+1)*config.GROUP_INTERVAL: return False
        if self.last and start_time1 > config.MAX_START_TIME: return False
        start_time2 = veh2_alloc_temp.order_list[-1].departure_time - veh2_alloc_temp.order_list[-1].order.load
        if self.last is False and start_time2 > (self.cur_batch+1)*config.GROUP_INTERVAL: return False
        if self.last and start_time2 > config.MAX_START_TIME: return False

        # cost
        original_cost = veh1.get_added_cost() + veh2.get_added_cost()
        new_cost = veh1_alloc_temp.get_added_cost() + veh2_alloc_temp.get_added_cost()
        if original_cost <= new_cost and not self.accept(original_cost, new_cost): return False


        # now swap!
        if config.DEBUG:
            write_solver_result(config.SWAP_SPATIAL_DIR, cost_delta=original_cost - new_cost,
                                route1=veh1.get_route(), route2=veh2.get_route(),
                                new_route1=veh1_alloc_temp.get_route(), new_route2=veh2_alloc_temp.get_route())

        veh1.order_list = veh1_temp
        veh2.order_list = veh2_temp
        veh1.update(); veh2.update()

        if self.simulated_annealing and self.solution.get_total_cost() < self.best_solution.get_total_cost():
            self.best_solution = copy.copy(self.solution)

        return True

    def swap_cycles(self):
        swapped = True
        cnt = 0

        comb = combinations(self.solution.vehicle_list, 2)
        while swapped and cnt < 200:
            swapped = False
            for veh1, veh2 in comb:
                if self.swap_cycle_try(veh1, veh2):
                    cnt += 1
                    swapped = True
        return cnt


    def swap_cycle_try(self, veh1, veh2) -> bool:

        for idx1 in range(len(veh1.cycle_list)):
            for idx2 in range(len(veh2.cycle_list)):
                if self.do_swap_cycle(veh1, idx1, veh2, idx2):
                    return True

        return False

    def do_swap_cycle(self, veh1, cycle1_idx, veh2, cycle2_idx) -> bool:
        try:
            cycle1 = veh1.cycle_list[cycle1_idx]
            cycle2 = veh2.cycle_list[cycle2_idx]
        except:
            return False

        # feasibility - cbm
        max1 = 0
        for order in cycle1.orders:
            max1 = max(order.cbm, max1)
        max2 = 0
        for order in cycle2.orders:
            max2 = max(order.cbm, max2)
        if max1 > veh2.vehicle.capa: return False
        if max2 > veh1.vehicle.capa: return False


        start_idx1 = start_idx2 = 0
        for i in range(cycle1_idx): start_idx1 += veh1.cycle_list[i].get_cycle_order_cnt()
        for j in range(cycle2_idx): start_idx2 += veh2.cycle_list[j].get_cycle_order_cnt()
        end_idx1 = start_idx1 + cycle1.get_cycle_order_cnt()
        end_idx2 = start_idx2 + cycle2.get_cycle_order_cnt()

        veh1_temp_list = copy.copy(veh1.order_list)
        veh2_temp_list = copy.copy(veh2.order_list)
        temp1 = copy.copy(veh1.order_list[start_idx1:end_idx1])
        temp2 = copy.copy(veh2.order_list[start_idx2:end_idx2])
        veh1_temp_list = list_insert(veh1_temp_list, start_idx1, end_idx1, temp2)
        veh2_temp_list = list_insert(veh2_temp_list, start_idx2, end_idx2, temp1)

        temp_veh1 = Vehicle_Alloc(veh1.vehicle, self.graph, veh1_temp_list)
        temp_veh2 = Vehicle_Alloc(veh2.vehicle, self.graph, veh2_temp_list)

        if temp_veh1.get_time_violation() + temp_veh2.get_time_violation() > 0: return False

        if len(temp_veh1.order_list) > 0:
            order_helper = temp_veh1.order_list[-1]
            start_time = order_helper.departure_time - order_helper.order.load
            if self.last is False and start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL: return False
            if self.last and start_time >= config.MAX_START_TIME: return False
        if len(temp_veh2.order_list) > 0:
            order_helper = temp_veh2.order_list[-1]
            start_time = order_helper.departure_time - order_helper.order.load
            if self.last is False and start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL: return False
            if self.last and start_time >= config.MAX_START_TIME: return False

        original_cost = veh1.get_added_cost() + veh2.get_added_cost()
        new_cost = temp_veh1.get_added_cost() + temp_veh2.get_added_cost()
        if new_cost >= original_cost and not self.accept(original_cost, new_cost): return False

        # now swap
        if config.DEBUG:
            write_solver_result(config.SWAP_CYCLE_DIR, cost_delta=original_cost - new_cost,
                                route1=veh1.get_route(), route2=veh2.get_route(),
                                new_route1=temp_veh1.get_route(), new_route2=temp_veh2.get_route())

        veh1.order_list = veh1_temp_list
        veh2.order_list = veh2_temp_list
        for veh in [veh1, veh2]: veh.update()

        if self.simulated_annealing and self.solution.get_total_cost() < self.best_solution.get_total_cost():
            self.best_solution = copy.copy(self.solution)

        return True

    def swap_orders(self):
        vehicle_list = self.solution.vehicle_list

        comb = combinations(vehicle_list, 2)

        swapped = True; cnt = 0
        while swapped and cnt < 200:
            swapped= False

            for veh1, veh2 in comb:
                for order1_idx in range(veh1.get_count()):
                    for order2_idx in range(veh2.get_count()):
                        if self.do_swap_order(veh1, order1_idx, veh2, order2_idx):
                            swapped = True
                            cnt += 1

        return cnt

    def do_swap_order(self, veh1, order1_idx, veh2, order2_idx):
        order1 = veh1.order_list[order1_idx]
        order2 = veh2.order_list[order2_idx]

        # feasibility check - cbm
        if order2.order.cbm > veh1.vehicle.capa: return False
        if order1.order.cbm > veh2.vehicle.capa: return False

        new_list1 = veh1.order_list.copy()
        new_list2 = veh2.order_list.copy()
        new_list1[order1_idx] = order2
        new_list2[order2_idx] = order1
        temp_veh1 = Vehicle_Alloc(veh1.vehicle, self.graph, new_list1)
        temp_veh2 = Vehicle_Alloc(veh2.vehicle, self.graph, new_list2)

        # feasibility check - time
        if temp_veh1.get_violation() + temp_veh2.get_violation() > 0: return False


        order_helper = temp_veh1.order_list[-1]
        start_time = order_helper.departure_time - order_helper.order.load
        if self.last is False and start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL: return False
        if self.last and start_time >= config.MAX_START_TIME: return False
        order_helper = temp_veh2.order_list[-1]
        start_time = order_helper.departure_time - order_helper.order.load
        if self.last is False and start_time > (self.cur_batch + 1) * config.GROUP_INTERVAL: return False
        if self.last and start_time >= config.MAX_START_TIME: return False

        # cost reduction check
        original_cost = veh1.get_added_cost() + veh2.get_added_cost()
        new_cost = temp_veh1.get_added_cost() + temp_veh2.get_added_cost()

        if new_cost >= original_cost and not self.accept(original_cost, new_cost):
            return False

        # swap
        if config.DEBUG:
            write_solver_result(config.SWAP_ORDER_DIR, cost_delta=original_cost - new_cost,
                                route1=veh1.get_route(), route2=veh2.get_route(),
                                new_route1=temp_veh1.get_route(), new_route2=temp_veh2.get_route())

        veh1.order_list[order1_idx] = order2
        veh2.order_list[order2_idx] = order1

        for veh in [veh1, veh2]:
            veh.update()

        if self.simulated_annealing and self.solution.get_total_cost() < self.best_solution.get_total_cost():
            self.best_solution = copy.copy(self.solution)

        return True

    def accept(self, prev_cost, cur_cost):
        # return False
        if not config.SIMULATED_ANNEALING: return False
        if not self.simulated_annealing: return False
        temperature = 100*math.exp(-10*(time.time() - self.start_sec)/self.allocated_time)
        exponent = (prev_cost - cur_cost - 1)/temperature
        exponent = max(-700, min(700, exponent))
        acceptance_prob = math.exp(exponent)
        if acceptance_prob > random.random():
            return True
        return False