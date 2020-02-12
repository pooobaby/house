#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright By Eric in 2020

import json
import requests
import pandas as pd
from tqdm.std import trange
from pymongo import MongoClient
from pyecharts import options as opts
from pyecharts.charts import Geo


class HouseMap(object):
    def __init__(self):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.house
        self.collection = self.db.Beike
        self.name, self.address, self.positions, self.list_n = [], [], [], []
        #　self.key = '高德地图API应用的KEY'
        self.datas = pd.DataFrame(self.collection.find())
        self.name = self.datas['name'].tolist()
        self.address = self.datas['address'].tolist()
        self.price = self.datas['price'].tolist()

    def house_data(self):
        dict_price, dict_position = {}, {}
        for i in trange(len(self.address)):
            url = 'https://restapi.amap.com/v3/geocode/geo?address=' + \
                  self.address[i] + '&key=' + self.key + '&city=沈阳'
            req = requests.get(url)
            data = json.loads(req.text)
            if data['count'] == '0':        # 去除不能生成地理位置坐标的数据
                continue
            pos = data['geocodes'][0]['location'].split(',')
            if float(pos[0]) == 0 or float(pos[1]) == 0:        # 去除坐标值为0的数据
                continue
            pos_lon_lat = [float(pos[0]), float(pos[1])]
            dict_position.update({self.name[i]: pos_lon_lat})
            dict_price.update(
                {self.name[i]: {'pos_lon_lat': pos_lon_lat, 'price': self.price[i]}})
        with open('position.json', 'w', encoding='utf-8') as f:     # 将坐标值写入json文件
            f.write(json.dumps(dict_position, ensure_ascii=False))
        with open('price.json', 'w', encoding='utf-8') as f:        # 将价格写入json文件
            f.write(json.dumps(dict_price, ensure_ascii=False))

    def visual(self):
        with open('price.json', 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        for n in data:
            price = data[n]['price']
            if not price.isdigit():     # 清除价格不规范的数据
                continue
            else:
                self.list_n.append((n, int(price)))
        house_map = (
            Geo(init_opts=opts.InitOpts(width='1200px', height='500px'))
            .add_schema(maptype="沈阳", center=[123.434039, 41.798102], zoom=6)
            # 从json文件导入坐标值
            .add_coordinate_json(r'position.json')
            .add('', self.list_n, symbol_size=10, color='#f20c00')
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            # 设置全局配置项
            .set_global_opts
            (
                visualmap_opts=opts.VisualMapOpts(type_='color', min_=5000, max_=18000),
                title_opts=opts.TitleOpts(title='沈阳市楼盘分布图',
                                          subtitle='数据来源：贝壳网(2020-01) 共{}个楼盘'.format(len(self.list_n))),
            )
            # 设置系列配置项
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        )
        return house_map


def main():
    housemap = HouseMap()
    housemap.house_data()
    housemap.visual().render('map_by_echart.html')
    print('数据地图生成完毕，请打开浏览器查看......')


if __name__ == '__main__':
    main()
