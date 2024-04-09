import pandas as pd
import argparse
import os
import datetime
import numpy as np

def preprocessing():

    args = parse_args()
    if args.raw:
        directory = os.path.join('data', 'raw')
        # 파일 불러오기
        terminals = pd.read_csv(os.path.join(directory, 'terminals.csv'), encoding='cp949')
        od_matrix = pd.read_csv(os.path.join(directory, 'od_matrix.csv'))
        veh_table = pd.read_csv(os.path.join(directory, 'vehicles.csv'))
        try: orders = pd.read_csv(os.path.join(directory, 'orders.csv'), encoding='cp949')
        except: orders = pd.read_csv(os.path.join(directory, 'orders.csv'))

        # 주문 데이터 가공
        orders['하차가능시간_시작'] = 60 * orders['하차가능시간_시작'].str[:-3].astype('Int64')
        orders['하차가능시간_종료'] = 60 * orders['하차가능시간_종료'].str[:-3].astype('Int64')
        orders.date = pd.to_datetime(orders.date)
        date_list = sorted(orders.date.unique())
        first_day = date_list[0]
        date = first_day; date_dict = {}; group = 0
        while True:
            date_dict[date] = group
            if date == max(date_list): break
            date += np.timedelta64(datetime.timedelta(hours=6))
            group += 1
        orders.Group = orders.date.map(date_dict) + orders.Group

        # 칼럼 순서 맞추기
        orders = orders[
            ['주문ID', '하차지_위도', '하차지_경도', '터미널ID', '착지ID', 'CBM', '하차가능시간_시작', '하차가능시간_종료', '하차작업시간_분', 'Group']]
        od_matrix = od_matrix[['origin', 'Destination', 'Distance_km', 'Time_minute']]
        veh_table = veh_table[['UserID', 'VehTon', 'BusinessStartTM', 'BusinessEndTM', 'MaxCapaCBM', 'StartCenter', 'FixedCost', 'VariableCost']]
        terminals = terminals[['ID', 'Origin_Lat', 'Origin_Lon', '상차지권역']]

        # 가공 데이터 저장
        directory = 'data'
        terminals.to_csv(os.path.join(directory, 'terminals.txt'), sep=' ', index=False, header=False)
        od_matrix.to_csv(os.path.join(directory, 'od_matrix.txt'), sep=' ', index=False, header=False)
        veh_table.to_csv(os.path.join(directory, 'vehicles.txt'), sep=' ', index=False, header=False)
        orders.to_csv(os.path.join(directory, 'orders.txt'), sep=' ', index=False, header=False)

        return pd.Timestamp(first_day).to_pydatetime()
    return pd.Timestamp(np.datetime64('2023-05-01')).to_pydatetime()

def parse_args():
    parser = argparse.ArgumentParser(description='Testing Files')
    parser.add_argument('-r', '--raw', dest='raw', action='store_true',
                        help = 'use_raw_data')
    args = parser.parse_args()
    return args