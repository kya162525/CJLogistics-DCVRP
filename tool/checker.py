import os
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings(action='ignore')


class checker:
    def __init__(self, dir_final, dir_vehicle_result, dir_od_matrix, dir_vehicles, dir_orders) -> None:
        self.final = pd.read_csv(dir_final)
        self.vehicle_result = pd.read_csv(dir_vehicle_result)
        self.od_matrix = pd.read_csv(dir_od_matrix)
        self.vehicles = pd.read_csv(dir_vehicles)
        try:
            self.orders = pd.read_csv(dir_orders)
        except:
            self.orders = pd.read_csv(dir_orders, encoding='cp949')

    def get_summary(self):
        success_order = set(self.final.query('Delivered=="Yes"').ORD_NO.unique())
        num_success = self.final.query('Delivered=="Yes"').ORD_NO.nunique()
        num_failed = len(set(self.orders['주문ID'].unique()).difference(success_order))
        num_vehicles = self.final.VehicleID.nunique()
        total_cost = self.vehicle_result.FixedCost.sum() + self.vehicle_result.VariableCost.sum()

        print("-------< Summary >-------")
        print("배송 완료   : ", num_success)
        print("베송 실패   : ", num_failed)
        print("사용한 차량 : ", num_vehicles)
        print("Total cost  : ", total_cost)
        print("-------------------------")

    def check_traveltime(self):
        print("터미널간 이동시간 제약 확인 중..")
        self.result_check = self.final.sort_values(by=['VehicleID', 'Sequence'])
        self.result_check['NextSiteCode'] = self.result_check.SiteCode.shift(-1)
        self.result_check['NextVeh'] = self.result_check.VehicleID.shift(-1)
        last_veh_idx = self.result_check[self.result_check['VehicleID'] != self.result_check['NextVeh']].index
        self.result_check.loc[last_veh_idx, 'NextSiteCode'] = np.nan
        result_temp = self.result_check.rename(columns={'SiteCode': 'origin', 'NextSiteCode': 'Destination'})
        result_temp = result_temp.merge(self.od_matrix[['origin', 'Destination', 'Time_minute', 'Distance_km']],
                                        how='left')
        result_temp['NextArrivalTime'] = result_temp['DepartureTime'] + result_temp['Time_minute']
        result_temp.NextArrivalTime = result_temp.NextArrivalTime.shift(1)
        result_temp = result_temp.rename(columns={'origin': 'SiteCode', 'Destination': 'NextSiteCode'})
        result_temp_drop = result_temp.drop_duplicates(subset=['VehicleID', 'ArrivalTime'], keep='first')

        violate_traveltime = result_temp_drop[
            (result_temp_drop['ArrivalTime'] < result_temp_drop['NextArrivalTime']) & (
                        result_temp_drop['NextSiteCode'].isna() == False)]
        if len(violate_traveltime) > 0:
            print(f"--> {len(violate_traveltime)}개 주문 터미널간 이동시간 제약 위반!")
            # print(violate_traveltime.ORD_NO)
        else:
            print("--> 터미널간 이동시간 제약 충족")

    def check_timewindow(self):
        print("하차 가능 시간 제약 확인 중..")
        self.result_check['ServiceStartTime'] = self.result_check['DepartureTime'] - self.result_check['ServiceTime']
        result_check2 = self.result_check  # .query('ORD_NO != "-1"')[['ORD_NO', 'ServiceStartTime']]
        result_check2['ServiceStartTime'] = result_check2['ServiceStartTime'] % 1440

        corner_idx = result_check2[result_check2['start'] > result_check2['end']].index
        normal_idx = result_check2[result_check2['start'] <= result_check2['end']].index

        corner_feasible_idx = result_check2[(result_check2['ServiceStartTime'] >= result_check2['start']) | (
                    result_check2['ServiceStartTime'] <= result_check2['end'])].index
        corner_feasible_idx = list(set(corner_idx).intersection(set(corner_feasible_idx)))
        result_check2.loc[corner_idx, 'feasibility'] = 0
        result_check2.loc[corner_feasible_idx, 'feasibility'] = 1

        normal_feasible_idx = result_check2[(result_check2['ServiceStartTime'] >= result_check2['start']) & (
                    result_check2['ServiceStartTime'] <= result_check2['end'])].index
        normal_feasible_idx = list(set(normal_idx).intersection(set(normal_feasible_idx)))
        result_check2.loc[normal_idx, 'feasibility'] = 0
        result_check2.loc[normal_feasible_idx, 'feasibility'] = 1

        violate_timewindow = result_check2.query('feasibility == 0')
        if len(violate_timewindow) > 0:
            print(f"--> {len(violate_timewindow)}개 주문 하차 가능 시간 제약 위반!")
            # print(violate_timewindow.ORD_NO)
        else:
            print("--> 하차 가능 시간 제약 충족")

    def check_72hours(self):
        print("72시간 제약 확인 중..")
        violate_72hours = self.final[
            (self.final['group'] != -1) & (self.final['group'] * 360 + 72 * 60 < self.final['DepartureTime'])]
        if len(violate_72hours) > 0:
            print(f"--> {len(violate_72hours)}개 주문 72시간 제약 위반!")
            # print(violate_72hours.ORD_NO)
        else:
            print("--> 72시간 제약 충족")

    def check_capa(self):
        print("Capacity 제약 확인 중..")
        result_check2 = self.result_check.reset_index(drop=True)
        check_idx = result_check2[
            (result_check2['VehicleID'] != result_check2['NextVeh']) | (result_check2['ORD_NO'] == "Null")].index

        check_list = []
        check_idx = sorted(check_idx)
        for num in range(len(check_idx) - 1):
            num1 = check_idx[num]
            num2 = check_idx[num + 1]
            veh = result_check2.loc[num1, 'VehicleID']
            res = result_check2.loc[num1:num2]['cbm'].sum() <= self.vehicles[self.vehicles['VehNum'] == veh][
                'MaxCapaCBM']
            if any(res) == False:
                check_list.append(num1)

        violate_capa = self.final.loc[check_list]
        if len(violate_capa) > 0:
            print(f"--> {len(violate_capa)}개 주문 Capacity 제약 위반!")
            # print(violate_capa.ORD_NO)
        else:
            print("--> Capacity 제약 충족")


if __name__ == "__main__":
    cls = checker(os.path.join("results", "final.csv"), os.path.join("results", "vehicle_result.csv"), os.path.join("data", "raw", "od_matrix.csv"),
                  os.path.join("data", "raw", "vehicles.csv"), os.path.join("data", "raw", "orders.csv"))
    cls.get_summary()
    cls.check_traveltime()
    cls.check_timewindow()
    cls.check_72hours()
    cls.check_capa()