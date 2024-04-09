import config
from object.graph import Graph
from object.order import Order
from object.vehicle import Vehicle
from tool.tools import can_time_cal, order_compute
from solution.Solution import Solution
from solution.helper import Veh_helper, Order_helper
from solution.vehicle_alloc import Vehicle_Alloc



class Initial_Solution_Generator:
    """
        For Batch
    """
    def __init__(self, graph:Graph, vehicle_list:list[Vehicle], order_list:list[Order], carry_over:bool, group: int):
        """

        :param graph:
        :param vehicle_list:
        :param order_list: orders to be dealt with at this batch
        :param carry_over: carry over to the next batch if
        :param group: this batch group number
        """

        self.graph = graph
        self.vehicle_list = [Veh_helper(veh) for veh in vehicle_list]
        self.order_list = [Order_helper(order) for order in order_list]
        self.carry_over = carry_over
        self.cur_batch = group

        if config.DEBUG and self.invalid():
            exit(1)

    def invalid(self):
        # no orders
        if len(self.order_list) == 0:
            print("no orders")
            return True

        return False

    def get_init_solution(self):
        """
        Solution 객체 형태로 초기해를 만들어서 리턴하는 함수 작성하면 됨!
        :return: Solution Object for Batch Problem
        """

        terminals = {}
        for order_helper in self.order_list:
            terminal = order_helper.order.terminal_id
            if terminal in terminals.keys(): terminals[terminal].append(order_helper)
            else: terminals[terminal] = [order_helper]
        terminals = dict(sorted(terminals.items(), key=lambda item: -len(item[1])))

        for terminal in terminals.keys():
            terminal_orders = terminals[terminal]
            self.terminal_alloc(terminal=terminal, orders=terminal_orders)

        vehicle_alloc_list = [ Vehicle_Alloc(vehicle=veh.vehicle, graph = self.graph, allocated_order_list=veh.allocated_order)  for veh in self.vehicle_list ]

        return Solution(graph = self.graph, order_list = self.order_list, vehicle_list= vehicle_alloc_list)


    def terminal_alloc(self, terminal, orders:list[Order_helper]):
        """
        The Kernel of Our Optimization,,
        :param orders: orders from this terminal
        :param terminal:
        :return:
        """
        vehicle_list = self.vehicle_list

        allocated = True
        while allocated:
            allocated = False

            left_orders = len(orders)
            for order in orders:
                if order.allocated: left_orders -= 1

            vehicle_list.sort(key=lambda x: (self.graph.get_time(x.cur_loc, terminal) + x.cur_time))
            if self.cur_batch + 1 != config.LAST_BATCH: vehicle_list = vehicle_list[:int(left_orders)]
            vehicle_list.sort(key=lambda x: self.graph.get_dist(x.cur_loc, terminal) * x.vehicle.vc + (
               x.vehicle.fc if x.vehicle.get_total_count() + len(x.allocated_order) == 0 else 0))

            for veh in vehicle_list:
                order_helper = self.next_order(veh, veh.cur_loc, veh.cur_time, veh.left, orders = orders, first=True)
                if order_helper is None: continue

                allocated = order_helper.allocated = True
                veh.allocated_order.append(order_helper)

                veh.left -= order_helper.order.cbm
                arrival_time = veh.cur_time + self.graph.get_time(veh.cur_loc, terminal) + \
                               self.graph.get_time(terminal, order_helper.order.dest_id)
                start_time = can_time_cal(arrival_time, order_helper.order.start, order_helper.order.end)
                veh.cur_time = start_time + order_helper.order.load
                veh.cur_loc = order_helper.order.dest_id
                order_helper.set_departure_time(start_time + order_helper.order.load)
                order_helper.set_arrival_time(arrival_time)


                while True:
                    order_helper = self.next_order(veh, veh.cur_loc, veh.cur_time, veh.left, orders = orders, first=False)
                    if order_helper is None: break
                    order_helper.allocated = allocated = True
                    veh.allocated_order.append(order_helper)
                    veh.left -= order_helper.order.cbm
                    if veh.cur_loc != order_helper.order.dest_id:
                        arrival_time = veh.cur_time + self.graph.get_time(veh.cur_loc, order_helper.order.dest_id)
                        start_time = can_time_cal(arrival_time, order_helper.order.start, order_helper.order.end)
                        veh.cur_time = start_time + order_helper.order.load
                        veh.cur_loc = order_helper.order.dest_id

                    start_time = can_time_cal(arrival_time, order_helper.order.start, order_helper.order.end)
                    order_helper.set_departure_time(start_time + order_helper.order.load)
                    order_helper.set_arrival_time(arrival_time)

                    veh.cur_time = max(veh.cur_time , start_time + order_helper.order.load)

            for veh in vehicle_list:
                veh.left = veh.vehicle.capa


    def next_order(self, veh, cur_loc, cur_time, left, orders:list[Order_helper], first):
        ret = None
        best_score = config.MAX
        if len(orders) > 0 and first:
            cur_time += self.graph.get_time(cur_loc, orders[0].order.terminal_id)
            cur_loc = orders[0].order.terminal_id

        for order_helper in orders:
            order = order_helper.order
            if order_helper.allocated or left < order.cbm or self.graph.get_time(cur_loc, order.dest_id) < 0:
                continue


            order_info = order_compute(graph=self.graph,
                                       cur_time = veh.allocated_order[-1].arrival_time if cur_loc == order.dest_id else cur_time,
                                       cur_loc = cur_loc,
                                       order_list = [order])
            order, arrival_time, start_time, departure_time = order_info[0]
            score = start_time
            if self.cur_batch - order.group >= 4: score -= config.MAX_START_TIME
            elif self.cur_batch - order.group >= 8: score -= config.MAX_START_TIME * 2


            if self.carry_over and first and \
                    (start_time-self.graph.get_time(cur_loc, order.dest_id) >= (self.cur_batch+1)*config.GROUP_INTERVAL): continue


            if departure_time - order.group*config.GROUP_INTERVAL >= config.TIME_CRITERION: continue

            if start_time < config.MAX_START_TIME and score < best_score:
                ret = order_helper
                best_score = score

        return ret