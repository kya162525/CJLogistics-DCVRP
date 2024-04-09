import math
import config


class Vehicle:
    def __init__(self, capa, fc, vc, veh_ton, start_center, veh_num, graph):
        """
            CONST
        """
        self.capa = capa
        self.fc = fc
        self.vc = vc
        self.veh_ton = veh_ton
        self.veh_num = veh_num
        self.start_center = start_center
        self.graph = graph
        self.sequence = 0

        """
            CONST in a batch
        """
        self.free_time = 0
        self.start_loc = start_center

        """
            Logging
        """
        self.allocated_cycle_list = []


    def __str__(self):
        total_cost = self.get_total_cost()
        fc = self.fc if len(self.allocated_cycle_list) > 0 else 0
        return f"{self.veh_num}," \
               f"{self.get_total_count()}," \
               f"{self.get_total_capa():.2f}," \
               f"{self.get_total_travel_distance():.2f}," \
               f"{self.get_total_spent_time():.2f}," \
               f"{self.get_total_travel_time():.2f}," \
               f"{self.get_total_service_time():.2f}," \
               f"{self.get_total_waiting_time():.2f}," \
               f"{total_cost:.2f}," \
               f"{fc:.2f}," \
               f"{total_cost - fc:.2f}\n"

    def __lt__(self, other):
        return self.free_time < other.free_time


    def allocate_vehicle(self, cycle_list): # cycle_list: list[Cycle]
        if len(cycle_list) == 0: return

        cur_time = self.free_time; cur_loc = self.start_loc; cur_sequence = self.sequence
        for cycle in cycle_list:
            cur_time, cur_loc, cur_sequence = cycle.get_after_info(start_time=cur_time, start_loc=cur_loc,
                                                    cur_sequence = cur_sequence, allocate=True)
            self.allocated_cycle_list.append(cycle)
        self.free_time = cur_time; self.start_loc = cur_loc; self.sequence = cur_sequence

    """
        Complex Methods
    """
    def get_total_route(self):
        if len(self.allocated_cycle_list) == 0: return []

        ret = []
        if self.allocated_cycle_list[0].terminal != self.start_center:
            ret.append(self.start_center)

        for cycle in self.allocated_cycle_list:
            ret.extend(cycle.get_cycle_route())

        return ret

    def get_total_capa(self):
        ret = 0
        for cycle in self.allocated_cycle_list:
            ret += cycle.get_cycle_capa()
        return ret

    def get_total_count(self):
        ret = 0
        for cycle in self.allocated_cycle_list:
            ret += cycle.get_cycle_order_cnt()
        return ret

    def get_total_travel_distance(self):
        route = self.get_total_route()
        ret = 0
        for i in range(1, len(route)):
            ret += self.graph.get_dist(route[i-1], route[i], cost=True)
        return ret

    def get_total_travel_time(self):
        route = self.get_total_route()
        ret = 0
        for i in range(1, len(route)):
            ret += self.graph.get_time(route[i-1], route[i])
        return ret

    def get_total_service_time(self):
        ret = 0
        for cycle in self.allocated_cycle_list:
            ret += cycle.get_cycle_service_time()
        return ret

    def get_total_cost(self):
        total_vc = self.vc * self.get_total_travel_distance()
        ret = total_vc + (self.fc if len(self.allocated_cycle_list)>0 else 0)
        return ret

    def get_total_waiting_time(self):
        return self.get_total_spent_time() - self.get_total_service_time() - self.get_total_travel_time()

    def get_total_spent_time(self):
        if len(self.allocated_cycle_list) == 0: return 0

        last_order = self.allocated_cycle_list[-1].orders[-1]
        return last_order.start_time + last_order.load


class Vehicle_Table:
    def __init__(self, file_dir, graph):
        self.table = []
        with open(file_dir) as f:
            for line in f:
                veh_num, veh_ton, _, _, capa, start_center, fc, vc = line.split()
                capa, fc, vc, veh_ton = map(float, [capa, fc, vc, veh_ton])
                start_center = graph.id2idx(start_center)
                vehicle = Vehicle(capa, fc, vc, veh_ton, start_center, veh_num, graph = graph)
                self.table.append(vehicle)

        self.table.sort()

    def __str__(self):
        return '\n'.join(str(vehicle) for vehicle in self.table)


    def write_order_result(self, dir, init=True):
        with open(dir, 'w' if init else 'a') as f:
            if init: f.write(config.ORDER_COLUMNS)

            for veh in self.table:
                for cycle in veh.allocated_cycle_list:
                    f.write(str(cycle))


    def write_veh_result(self):
        with open(config.VEH_RESULT_DIR, 'w') as f:
            f.write(config.VEH_COLUMNS)
            for veh in self.table:
                f.write(str(veh))

    def update_allocated_orders(self, cur_time):
        for veh in self.table:
            for cycle in veh.allocated_cycle_list:
                cycle.update_orders(cur_time)

    def update_freetime(self, cur_time):
        for veh in self.table:
            veh.free_time = max(veh.free_time, cur_time)

    def get_total_cost(self):
        ret = 0.0
        for veh in self.table: ret += veh.get_total_cost()
        return ret


