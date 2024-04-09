"""import config
from object.graph import Graph
from solution.vehicle_alloc import Vehicle_Alloc


class spatial_candidate:

    def __init__(self, graph:Graph, vehicle_alloc_list:list[Vehicle_Alloc]):
        self.graph = graph
        self.vehicle_alloc_list = vehicle_alloc_list

    def update(self, vehicle_alloc_list:list[Vehicle_Alloc]):
        self.vehicle_alloc_list = vehicle_alloc_list

    def get_candidates(self):

        ret = [] # (bundle

        for i, veh_alloc in enumerate(self.vehicle_alloc_list):
            # consider close vehicle only
            friends = []
            for j , friend in enumerate(self.vehicle_alloc_list):
                if self.graph.get_dist(veh_alloc.vehicle.start_loc, friend.vehicle.start_loc) < config.SPATIAL_BUNDLE_CRITERION:
                    friends.append(friend)

            my_bundle = veh_alloc.spatial_bundle
            for friend in friends:
                spaital_bundles = friend.spatial_bundle
                if ()
"""
