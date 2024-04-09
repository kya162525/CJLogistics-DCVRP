import itertools
import math
from collections import deque
import random

import config
from object.graph import Graph


def can_time_cal(arrival_time, start: int, end: int):
    quotient = int(arrival_time // config.DAY)
    remainder = arrival_time % config.DAY

    if start < end:
        if start <= remainder <= end:
            return arrival_time
        elif remainder < start:
            return quotient * config.DAY + start
        else:  # end < remainder
            return (quotient + 1) * config.DAY + start
    else:
        if end < remainder < start:
            return quotient * config.DAY + start
        else:
            return arrival_time


def euclidean_distance(loc1:(float, float), loc2: (float, float)) -> float:
    scaling_factor = 111

    dx = abs(loc1[0] - loc2[0]); dy = abs(loc1[1] - loc2[1])
    dx *= scaling_factor; dy *= scaling_factor
    return (dx**2 + dy**2)**0.5

def deque_slice(deq:deque, start_idx = 0, end_idx = None):
    return deque(itertools.islice(deq, start_idx, end_idx))


def list_insert(to:list, from_idx:int, to_idx:int, items:list)->list:
    return to[:from_idx] + items + to[to_idx:]

def list_delete(lst:list, from_idx:int ,to_idx) -> list:
    return lst[:from_idx] + lst[to_idx:]

def time_check(order_list, time_limit:int, last:bool): # order_helper list
    if len(order_list) == 0: return True

    order_helper = order_list[-1]
    start_time = order_helper.departure_time - order_helper.order.load

    if last:
        return start_time <= config.MAX_START_TIME
    else:
        return start_time <= time_limit


def random_combinations(lst:list, r:int, graph:Graph):
    all_combinations = list(itertools.combinations(lst, r))

    def fun(veh_tuple):
        veh1 = veh_tuple[0]
        veh2 = veh_tuple[1]

        no = (len(veh1.order_list) == 0) and (len(veh2.order_list) == 0)

        return (1 if no else 0,
                euclidean_distance(
                    graph.get_coordinates(veh1.vehicle.start_loc),
                    graph.get_coordinates(veh2.vehicle.start_loc)
                )
        )

    all_combinations.sort(key = lambda x : fun(x))

    idx = 0
    for i, comb in enumerate(all_combinations):
        veh1 = comb[0]; veh2 = comb[1]
        if (len(veh1.order_list) ==0) and (len(veh2.order_list) == 0):
            break
        else:
            idx += 1
    return all_combinations[:idx]

def veh_combination(veh_list): # vehicle alloc
    n = len(veh_list)
    ret = [] # (veh1, veh2)

    for i in range(n):
        for j in range(i+1, n):
            veh1 = veh_list[i]; veh2 = veh_list[j]
            if len(veh1.order_list) ==0 and len(veh2.order_list)==0:
                continue
            ret.append((veh1, veh2))
    return ret

def order_compute(cur_time, cur_loc, order_list, graph):
    """
    A singleton cycle only
    :param cur_time:
    :param cur_loc:
    :param order_list: [Order]
    :param graph:
    :return:
    """
    ret = [(order, -1,-1,-1) for order in order_list]

    arrival_time = cur_time
    for i, order in enumerate(order_list):
        if order.dest_id == cur_loc:
            start_time = can_time_cal(arrival_time, order.start, order.end)
            end_time = start_time + order.load

        else:
            arrival_time = cur_time + graph.get_time(cur_loc, order.dest_id)
            start_time = can_time_cal(arrival_time, order.start, order.end)
            end_time = start_time + order.load

        ret[i] = (ret[i][0], arrival_time, start_time, end_time)

        cur_time = max(cur_time, end_time)
        cur_loc = order.dest_id
    return ret

def write_solver_result(dir:str, cost_delta, route1, new_route1, route2=[], new_route2=[], veh1:str="veh1", veh2:str="veh2"):
    """
    "COST_DELTA,ROUTE1,ROUTE2,NEW_ROUTE1,NEW_ROUTE2"
    """
    with open(dir, 'a') as f:
        f.write(str(cost_delta)); f.write(',')
        f.write('|'.join(str(item) for item in route1) + veh1); f.write(',')
        f.write('|'.join(str(item) for item in route2) + veh2); f.write(',')
        f.write('|'.join(str(item) for item in new_route1) + veh1); f.write(',')
        f.write('|'.join(str(item) for item in new_route2) + veh2);f.write('\n')


