import os

DEBUG = True
INTEGER = True
SIMULATED_ANNEALING = True

HOUR = 60
DAY = HOUR*24
WEEK = DAY*7

MAX = 987654321
GRAPH_SIZE = 2000
LAST_BATCH = 12                       # check
GROUP_INTERVAL = 360
MAX_TIME = LAST_BATCH * GROUP_INTERVAL + DAY
MAX_START_TIME = MAX_TIME - 60                  # check - 60
TIME_CRITERION = DAY * 3
TEMPORAL_BUNDLE_CRITERION = 100
SPATIAL_BUNDLE_CRITERION = 100

TIMELIMIT_SEC = 60*8                            # check
NUM_ITER = 30
TIME_CONSTRAINT = 60*90
TIMEOUT = -1

ORDER_ID_NULL = "Null"
STRING_NULL = "Null"
TERMINAL_START_CHARACTER = "O"
DEST_START_CHARACTER = "D"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

"""
        RESULT_FILE
"""
FINAL_ORDER_RESULT_DIR = os.path.join("results", "final.csv")
ORDER_RESULT_DIR = os.path.join("results", "order_result.csv")
VEH_RESULT_DIR = os.path.join("results", "vehicle_result.csv")
IDX2ID_DIR = os.path.join("results", "id2idx.csv")
COORDINAES_DIR = os.path.join("results", "coordinates.csv")

DISTRIBUTION_DIR = os.path.join("results", "distribution.csv")
SWAP_VEHICLE_DIR = os.path.join("results", "swap_vehicles.csv")
SWAP_SPATIAL_DIR = os.path.join("results", "swap_spatial.csv")
SWAP_CYCLE_DIR = os.path.join("results", "swap_cycles.csv")
SWAP_ORDER_DIR = os.path.join("results", "swap_order.csv")
SOLVER_DIRS = [DISTRIBUTION_DIR, SWAP_ORDER_DIR, SWAP_SPATIAL_DIR, SWAP_CYCLE_DIR, SWAP_VEHICLE_DIR]
SOLVER_COLUMNS = "COST_DELTA,ROUTE1,ROUTE2,NEW_ROUTE1,NEW_ROUTE2"
"""
        DATA
"""
ORDERS = os.path.join("data", "orders.txt")
OD_MATRIX = os.path.join("data", "od_matrix.txt")
TERMINALS = os.path.join("data", "terminals.txt")
VEHICLES = os.path.join("data", "vehicles.txt")

ORDER_COLUMNS =\
        "ORD_NO," + \
        "VehicleID," + \
        "Sequence," + \
        "SiteCode," + \
        "ArrivalTime," + \
        "WaitingTime," + \
        "ServiceTime," + \
        "DepartureTime," + \
        "Delivered," + \
        "cbm," + \
        "start," + \
        "end," + \
        "group\n" \
        if DEBUG else \
        "ORD_NO," + \
        "VehicleID," + \
        "Sequence," + \
        "SiteCode," + \
        "ArrivalTime," + \
        "WaitingTime," + \
        "ServiceTime," + \
        "DepartureTime," + \
        "Delivered\n"

VEH_COLUMNS = \
        "VehicleID," + \
        "Count," + \
        "Volume," + \
        "TravelDistance," + \
        "WorkTime," + \
        "TravelTime," + \
        "ServiceTime," + \
        "WaitingTime," + \
        "TotalCost," + \
        "FixedCost," + \
        "VariableCost\n"

