import copy

import config
from object.Cycle import Cycle
from object.bundle import Spatial_bundle
from object.graph import Graph
from object.vehicle import Vehicle
from tool.tools import can_time_cal, order_compute
from solution.helper import Order_helper
from collections import deque
from itertools import islice


class Vehicle_Alloc:

    def __copy__(self):
        allocated_order_list_copy = [ copy.copy(order_helper) for order_helper in self.order_list]
        return Vehicle_Alloc(vehicle=self.vehicle, graph=self.graph, allocated_order_list= allocated_order_list_copy)

    def __init__(self, vehicle:Vehicle, graph:Graph, allocated_order_list:list[Order_helper]):
        self.graph = graph
        self.vehicle = vehicle # const
        self.order_list = allocated_order_list # temp list, not including terminal loading order (-1)
        self.cycle_list = [] #
        self.spatial_bundle = []
        self.update()

        # cache
        self.route_cache = [-1]
        self.dist_cache = -1
        self.work_cache = -1
        self.max_capa_cache = -1
        self.after_time_cache = -1
        self.capa_violation_cache = -1
        self.time_violation_cache = -1


    """
    When any modifications are made to the "self.order_list",
    update must be called
    """

    def update(self):
        self.reset_cache()
        # self.update_temporal_bundle()
        self.update_cycle()
        self.update_spatial_bundle()

    def update_cycle(self):
        self.cycle_list = []
        if len(self.order_list) == 0: return

        temp_orders = []
        left = self.vehicle.capa
        cur_terminal = -1

        ##################### cycle bundling with capa only #####################
        for order_helper in self.order_list:
            order = order_helper.order
            # terminal loading
            if cur_terminal != order.terminal_id or left < order.cbm:
                if cur_terminal != -1:
                    self.cycle_list.append(Cycle(copy.copy(temp_orders), self.vehicle, self.graph))
                cur_terminal = order.terminal_id
                left = self.vehicle.capa
                temp_orders = []
            left -= order.cbm
            temp_orders.append(order)

        # last one
        self.cycle_list.append(Cycle(temp_orders, self.vehicle, self.graph))


        #######################################################################

        cur_loc = self.vehicle.start_loc; cur_time = self.vehicle.free_time
        idx = 0

        for cycle in self.cycle_list:
            cur_time += self.graph.get_time(cur_loc, cycle.terminal)
            cur_loc = cycle.terminal
            order_infos = order_compute(graph=self.graph, order_list=cycle.orders, cur_loc = cur_loc, cur_time = cur_time)
            for order_info in order_infos:
                order_helper = self.order_list[idx]; idx+=1
                order, arrival_time, start_time, end_time = order_info
                order_helper.set_departure_time(end_time)
                order_helper.set_arrival_time(arrival_time)

    def update_spatial_bundle(self):
        self.spatial_bundle = []
        if len(self.order_list) == 0: return

        temp_orders = [self.order_list[0].order]
        cur_loc = self.order_list[0].order.dest_id

        for order_helper in deque(islice(self.order_list,1, None)):

            order = order_helper.order
            if self.graph.get_dist(cur_loc, order.dest_id) > config.TEMPORAL_BUNDLE_CRITERION:
                self.spatial_bundle.append(
                    Spatial_bundle(graph=self.graph, vehicle=self.vehicle, orders=copy.copy(temp_orders)))
                temp_orders = []
            cur_loc = order.dest_id
            temp_orders.append(order)

        # last one
        self.spatial_bundle.append(
            Spatial_bundle(graph=self.graph, vehicle=self.vehicle, orders=copy.copy(temp_orders)))
        return

    def reset_cache(self):
        self.route_cache = [-1]
        self.dist_cache = -1
        self.work_cache = -1
        self.max_capa_cache = -1
        self.after_time_cache = -1
        self.capa_violation_cache = -1
        self.time_violation_cache = -1

    """
           Complex Methods
    """

    def get_route(self):
        """
            In this batch problem, the 'start_loc' (which might be determined during the previous batch problem)
            moves to the 'final loc' (the next 'start_loc').

            it assumes that the self.cycle_list has been updated earlier

            No duplicates!
            ex) [1, 3, 3, 4] X, [1, 3, 4] O

        :return: [1,5,7,2,7,8..] (including terminal loading)
        """

        # caching
        if self.route_cache[0] != -1: return self.route_cache
        if len(self.cycle_list) == 0: return []

        ret = []
        if self.cycle_list[0].terminal != self.vehicle.start_loc:
            ret.append(self.vehicle.start_loc)

        for cycle in self.cycle_list:
            ret.extend(cycle.get_cycle_route())

        self.route_cache = ret
        return copy.deepcopy(self.route_cache)

    def get_travel_distance(self):
        # caching
        if self.dist_cache != -1: return self.dist_cache
        route = self.get_route()
        if len(route) == 0: return 0

        ret = 0
        cur = route[0]
        for next in route[1:]:
            ret += self.graph.get_dist(cur, next)
            cur = next

        self.dist_cache = ret
        return self.dist_cache

    def get_travel_time(self):
        # caching
        if self.dist_cache != -1: return self.dist_cache
        route = self.get_route()
        if len(route) == 0: return 0

        ret = 0
        cur = route[0]
        for next in route[1:]:
            ret += self.graph.get_time(cur, next)
            cur = next

        self.dist_cache = ret
        return self.dist_cache

    # variable cost only
    def get_var_cost(self):
        return self.get_travel_distance() * self.vehicle.vc

    def get_added_cost(self):
        var_cost = self.get_var_cost()
        if len(self.vehicle.allocated_cycle_list) == 0 and len(self.order_list) > 0:
            return var_cost + self.vehicle.fc
        else:
            return var_cost

    # order count
    def get_count(self):
        return len(self.order_list)

    def get_service_time(self):
        # caching
        if self.work_cache != -1: return self.work_cache

        ret = 0
        for order_helper in self.order_list: ret += order_helper.order.load

        self.work_cache = ret
        return self.work_cache

    def get_max_capa(self):
        # caching
        if self.max_capa_cache != -1: return self.max_capa_cache
        if len(self.order_list) == 0: return 0

        ret = 0
        for cycle in self.cycle_list:
            ret = max(ret, cycle.total_capa)
        return ret

    def get_after_time(self):
        # caching
        if self.after_time_cache != -1: return self.after_time_cache


        cur_time = self.vehicle.free_time
        cur_loc = self.vehicle.start_loc
        for cycle in self.cycle_list:
            cur_time, cur_loc = cycle.get_after_info(start_time = cur_time, start_loc=cur_loc)

        self.after_time_cache = cur_time
        return self.after_time_cache

    def get_spent_time(self):
        return self.get_after_time() - self.vehicle.free_time

    def get_waiting_time(self):
        return self.get_spent_time() - self.get_travel_time() - self.get_work_time()


    """
        Violation
    """
    def get_capa_violation(self):
        """
        capa 제한 넘은 무게들의 합
        :return:
        """
        if self.capa_violation_cache != -1:
            return self.capa_violation_cache

        ret = 0; capa = self.vehicle.capa
        for cycle in self.cycle_list:
            ret += max(0, cycle.total_capa - capa)

        self.capa_violation_cache = ret
        return self.capa_violation_cache

    def get_time_violation(self):
        """
        :return: 주문 할당 ~ 처리까지 24시간 초과 시간들의 합
       합"""
        if self.time_violation_cache != -1:
            return self.time_violation_cache
        ret = 0

        for order_helper in self.order_list:
            order = order_helper.order
            allocated_time = order.group * config.GROUP_INTERVAL
            spent_time = order_helper.departure_time - allocated_time
            ret += max(0, spent_time - config.TIME_CRITERION)

        self.time_violation_cache = ret
        return self.time_violation_cache

    def get_violation(self):
        return self.get_time_violation() + self.get_capa_violation()



