import config
from config import *
from object.vehicle import Vehicle
from tool.tools import can_time_cal


class Order:

    def __init__(self, dest_id, order_id = ORDER_ID_NULL,
                 terminal_id = -1, latitude=-1.0, longitude=-1.0, cbm=0.0,
                 load=0, group=-1, start=0, end=DAY):
        self.order_id = order_id #str
        self.terminal_id = terminal_id #int idx
        self.dest_id = dest_id #int idx
        self.latitude = latitude
        self.longitude = longitude
        self.cbm = cbm # double
        self.load = load # double? int ?
        self.group = group # 0~23
        self.start = start # 0~1440
        self.end = end # 0 ~ 1440

        # for optimization
        self.prev_free = -1
        self.next_arrival = -1

        # for logging
        self.vehicle = None
        self.serviced = self.delivered = False
        self.arrival_time = -1
        self.start_time = -1
        self.sequence = -1

    def get_coordinates(self):
        return self.latitude, self.longitude

    def allocate(self, arrival_time:int, vehicle:Vehicle, sequence):
        self.serviced = True
        self.arrival_time = arrival_time
        self.vehicle = vehicle
        self.start_time = can_time_cal(arrival_time, self.start, self.end)
        self.sequence = sequence

    def update(self, cur_time:int):
        if self.serviced and (self.start_time + self.load <= cur_time):
            self.delivered = True


    def __str__(self):
        allocated = self.sequence != -1
        seperator = ","
        sb = []

        terminal_order = (self.order_id == STRING_NULL)

        sb.append(str(self.order_id))
        sb.append(str(self.vehicle.veh_num) if allocated else config.STRING_NULL)
        sb.append(str(self.sequence) if allocated else config.STRING_NULL) # sequence
        sb.append(str(self.dest_id) if allocated else config.STRING_NULL) # site code !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        if self.delivered:
            sb.append(str(self.arrival_time) if allocated else config.STRING_NULL) # arrival
            sb.append(str(self.start_time - self.arrival_time) if allocated else config.STRING_NULL) # wating
            sb.append(str(self.load) if allocated else config.STRING_NULL) # service
            sb.append(str(self.start_time + self.load) if allocated else config.STRING_NULL) # departure
            sb.append((STRING_NULL if terminal_order else "Yes") if allocated else config.STRING_NULL)
        else:
            sb.append(STRING_NULL)
            sb.append(STRING_NULL)
            sb.append(STRING_NULL)
            sb.append(STRING_NULL)
            sb.append((STRING_NULL if terminal_order else "No") if allocated else config.STRING_NULL)

        if DEBUG:
            sb.append(str(self.cbm))
            sb.append(str(self.start))
            sb.append(str(self.end))
            sb.append(str(self.group))
        return seperator.join(sb)


class OrderTable:
    def __init__(self, file_dir=None, graph=None):
        self.table = [[] for _ in range(LAST_BATCH)]
        self.graph = graph
        if file_dir is not None and graph is not None:
            self.initialize(file_dir, graph)

    def initialize(self, file_dir, graph):
        try:
            with open(file_dir, 'r') as fs:
                for line in fs:
                    data = line.split()
                    order_id = data[0]
                    latitude = float(data[1])
                    longitude = float(data[2])
                    terminal_id = data[3]
                    dest_id = data[4]
                    cbm = float(data[5])
                    start = int(data[6])
                    end = int(data[7])
                    load = int(data[8])
                    group = int(data[9])

                    if group < config.LAST_BATCH:

                        dest_idx = graph.id2idx(dest_id)
                        self.table[group].append(
                            Order(order_id = order_id,
                                  terminal_id= graph.id2idx(terminal_id),
                                  dest_id= dest_idx,
                                  latitude = latitude,
                                  longitude = longitude,
                                  cbm= cbm,
                                  load = load,
                                  group= group,
                                  start = start,
                                  end = end
                                  )
                        )
                        self.graph.coordinates[dest_idx] = (latitude, longitude)
        except FileNotFoundError:
            print(f"invalid directories : {file_dir}")
            exit(1)

    def update_orders(self, cur_time:int):
        for batch in self.table:
            for order in batch:
                order.update(cur_time)

    def __str__(self):
        total_service = total_not = 0
        sb = []

        for group, order_group in enumerate(self.table):
            serviced_cnt = not_cnt = 0
            for order in order_group:
                if order.serviced: serviced_cnt += 1
                else: not_cnt += 1

            sb.append(f"batch {group} : ( {serviced_cnt} , {not_cnt} )")
            total_service += serviced_cnt
            total_not += not_cnt
        sb.append(f"{total_service}, {total_not}")

        return "\n".join(sb)


