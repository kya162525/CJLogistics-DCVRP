from object.graph import Graph
from object.order import Order
from object.vehicle import Vehicle


class Spatial_bundle:
    def __init__(self, orders:list[Order], vehicle:Vehicle, graph:Graph):
        self.graph = graph
        self.orders = orders
        self.vehicle = vehicle
        self.terminal = orders[0].terminal_id

        self.center = (0.0, 0.0)
        size = len(self.orders)
        for order in self.orders:
            self.center += (order.latitude, order.longitude)
        self.center = (self.center[0] / size, self.center[1] / size)

    def get_center(self):
        return self.center

    def get_size(self):
        return len(self.orders)
