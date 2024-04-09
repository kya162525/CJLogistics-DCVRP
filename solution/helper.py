from object.order import Order
from object.vehicle import Vehicle


class Order_helper:
    def __init__(self, order:Order):
        self.order = order
        self.allocated = False
        self.departure_time = -1
        self.arrival_time = -1

    def set_departure_time(self, departure_time):
        self.departure_time = departure_time
    def set_arrival_time(self, arrival_time):
        self.arrival_time = arrival_time

class Veh_helper:
    def __init__(self, vehicle: Vehicle):
        self.vehicle = vehicle
        self.cur_loc = vehicle.start_loc
        self.cur_time = vehicle.free_time
        self.left = vehicle.capa
        self.allocated_order = []
