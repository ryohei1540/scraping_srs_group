# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from urllib import request
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import sqlalchemy


def main(event, context):
    url = "https://srs-holdings.co.jp/ir/library/monthly/"
    html = request.urlopen(url)
    soup = BeautifulSoup(html, "html.parser")
    header_df = scrape_header(soup)
    data_df = scrape_data(soup)
    comp_df = header_df.groupby('YM', as_index=False).\
        apply(merge_df, data_df=data_df).assign(createdAt=datetime.now())
    import_cloud_sql(comp_df)


def scrape_header(soup):
    rows = soup.find_all("table", class_="ir10")[0].findAll("th")
    restaurant_list =\
        [row.get_text() for row in rows
         if is_restaurant(row) if row.get_text().strip()]
    df = pd.DataFrame(get_header_dict(restaurant_list)).\
        assign(salesPercent=np.nan,
               customerNumPercent=np.nan,
               avgSpendPercent=np.nan)
    return df


def scrape_data(soup):
    rows = soup.find_all("table", class_="ir10")[0].findAll("td")
    dd = defaultdict(list)
    for row in rows:
        target_str = row.string
        if target_str is None:
            target_str = '0'
        elif not target_str.strip():
            continue
        if is_month(target_str):
            not_target = False
            target_month = int(re.sub("\\D", "", target_str))
            target_year = 2019 if 4 <= target_month <= 12 else 2020
            target_date = date(target_year, target_month, 1).strftime('%Y-%m')
            continue
        if not_target:
            continue
        if is_half_or_full_year(target_str):
            not_target = True
            continue
        dd[target_date].append(target_str)
    data_df = pd.DataFrame(dd).rename(index={0: '全店-salesPercent',
                                             1: '和食さと-salesPercent',
                                             2: '和食さと-customerNumPercent',
                                             3: '和食さと-avgSpendPercent',
                                             4: 'にぎり長次郎-salesPercent',
                                             5: 'にぎり長次郎-customerNumPercent',
                                             6: 'にぎり長次郎-avgSpendPercent'})
    return data_df


def get_header_dict(restaurant_list):
    header_dict = {}
    header_dict['companyName'] = ['SRSグループ'] * 36
    header_dict['isGroup'] =\
        [True if r == '全店' else False for r in restaurant_list] * 12
    header_dict['restaurantName'] = restaurant_list * 12
    date_year_list =\
        [date(2019, 4, 1) + relativedelta(months=x) for x in range(0, 12)]
    header_dict['YM'] =\
        [result.strftime('%Y-%m') for month in date_year_list
         for result in [month] * 3]
    return header_dict


def is_restaurant(row):
    if 'rowspan' in row.attrs:
        return True
    return False


def is_month(target_str):
    if target_str[-1] == '月':
        return True
    return False


def is_half_or_full_year(target_str):
    if target_str in ['上期', '下期', '通期']:
        return True
    return False


def merge_df(header_df, data_df):
    target_date = header_df.YM.values[0]
    value_series = data_df[target_date].to_list()
    r_name_column_lists = data_df[target_date].index.str.split('-')
    for r_name_column_list, v in zip(r_name_column_lists, value_series):
        header_df.loc[(header_df.restaurantName == r_name_column_list[0]),
                      r_name_column_list[1]] = v
    return header_df


def import_cloud_sql(df):
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    db = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL(
            drivername='mysql+pymysql',
            username=db_user,
            password=db_pass,
            database=db_name,
            query={
                'unix_socket': '/cloudsql/{}'.format(cloud_sql_connection_name)
            }
        )
    )
    df.to_sql('restaurants', db, index=False, if_exists='append')
