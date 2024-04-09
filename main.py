import os.path

import config
from proc.postprocessing import post_processing

from tool.checker import checker
from simulator.program import Program
from proc.preprocessing import preprocessing

if __name__ == "__main__":

    first_date = preprocessing()
    program = Program()
    program.simulator()

    ch = checker(dir_final=config.FINAL_ORDER_RESULT_DIR,
            dir_vehicles=os.path.join("data", "raw", "vehicles.csv"),
            dir_od_matrix= os.path.join("data", "raw", "od_matrix.csv"),
            dir_vehicle_result= config.VEH_RESULT_DIR,
            dir_orders= os.path.join("data", "raw", "orders.csv"))

    ch.get_summary()
    post_processing(first_date = first_date)
