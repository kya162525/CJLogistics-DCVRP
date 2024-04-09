import datetime
import os

import pandas as pd
import config
import numpy as np

def post_processing(first_date:datetime.datetime):
    dfs = []
    for i in range(config.LAST_BATCH):
        try: df = pd.read_csv(os.path.join("results", f"order_result{i}.csv"), encoding='cp949')
        except: df = pd.read_csv(os.path.join("results", f"order_result{i}.csv"))
        dfs.append(( os.path.join("results", f"order_result{i}.csv"), df))
    dfs.append((config.FINAL_ORDER_RESULT_DIR ,pd.read_csv(config.FINAL_ORDER_RESULT_DIR)))

    idx2id = pd.read_csv(config.IDX2ID_DIR, index_col = 'IDX')
    for dir, df in dfs:
        """
            PostProcessing
        """
        df['SiteCode'] = df['SiteCode'].apply(lambda x : idx2id.loc[int(x),'ID'] if x != config.STRING_NULL else x)

        cols = ['ArrivalTime', 'DepartureTime']
        for col in cols:
            df[col] = df[col].apply(lambda x : (first_date + datetime.timedelta(minutes=int(x))).strftime(config.DATETIME_FORMAT)
                                    if x != config.STRING_NULL else x)

        df.to_csv(dir, index=False)

