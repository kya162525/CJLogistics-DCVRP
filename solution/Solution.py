import copy

from object.order import Order
from object.graph import Graph
from solution.helper import Order_helper
from solution.vehicle_alloc import Vehicle_Alloc


class Solution:
    """
        General Solution Frame
    """

    def __copy__(self):
        vehicle_list = [ copy.copy(veh_alloc) for veh_alloc in self.vehicle_list]
        return Solution(graph = self.graph, vehicle_list = vehicle_list, order_list = self.order_list)

    def __init__(self, graph:Graph, vehicle_list:list[Vehicle_Alloc], order_list:list[Order_helper]):
        """
        :param graph:
        :param vehicle_list: The list of vehicles to be considered.
            For the terminal problem, it could be the top N vehicles sorted by their spatial closeness.
            For the batch problem, it includes all the vehicles.
        :param order_list: The list of orders to be dealt with.
            For the terminal problem, it includes every order starting in a certain terminal (excluding ones that have been carried over to the next batch).
            For the batch problem, it includes every order in a batch (excluding ones that have been carried over to the next batch).
        """

        """
            CONST
            for reference only
        """
        self.graph = graph
        self.order_list = order_list

        """
            improve it!
        """
        self.vehicle_list = vehicle_list

    def __str__(self):
        return f"capa({self.get_capa_violation_score()}), time({self.get_time_violation_score()})"

    def allocate_solution(self):
        for veh_alloc in self.vehicle_list:
            veh_alloc.vehicle.allocate_vehicle(veh_alloc.cycle_list)


    def update(self):
        """
            Whenever any modification was made, must be called
        """
        for veh in self.vehicle_list:
            veh.update_cycle()

    def get_var_cost(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_var_cost()
        return ret

    def get_total_cost(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_added_cost()
            # ret += veh.vehicle.get_total_cost()
            # if veh.vehicle.get_total_count() == 0 and veh.get_count() > 0: ret += veh.vehicle.fc
        return ret

    def get_total_waiting_time(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_waiting_time()
        return ret

    def get_total_spent_time(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_spent_time()
        return ret

    def get_capa_violation_score(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_capa_violation()
        return ret

    def get_time_violation_score(self):
        ret = 0
        for veh in self.vehicle_list:
            ret += veh.get_time_violation()
        return ret




