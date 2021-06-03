# import akshare as ak
# from akshare.stock.cons import zh_sina_a_stock_payload
#
# zh_sina_a_stock_payload.update({"symbol": "sh510300"})
# stock_zh_a_spot_df = ak.stock_zh_a_spot()
# print(stock_zh_a_spot_df)

import datetime
# print(datetime.datetime.now().year)
# print(datetime.datetime.now().month)
# print(datetime.datetime.now().day)

# 当前报告期
import os
import webbrowser

from jinja2 import Environment, FileSystemLoader

report_date = '2021-03-31'
# 当前日月
# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# current = m * 100 + d
find_date = ''

# # 计算最近的报告期
# report_dates = {331: '03-31', 630: '06-30', 930: '09-30', 1231: '12-31'}
# # 当前日月
# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# current = 212 #m * 100 + d
#
# count = 0
# for key, value in report_dates.items():
#     if key < current:
#         count += 1
#         continue
#
#     find_date = list(report_dates.values())[count - 1]
#     break
#
# print(find_date)
import time

# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# t = datetime.datetime(y, m, d)
# print(t.toordinal())
# print((t-datetime.datetime(1970,1,1)).total_seconds())

# print(str(int(round(time.time() * 1000))))

# from pyecharts import options as opts
# from pyecharts.charts import Radar
# v1=[[120,112,45,50,70,90,20,30]]   # 数据必须为二维数组，否则会集中一个指示器显示
# v2=[[80,90,120,50,60,85,5,15]]
# radar1=(
#     Radar()
#     .add_schema(# 添加schema架构
#         schema=[
#             opts.RadarIndicatorItem(name='ability1',max_=150),# 设置指示器名称和最大值
#             opts.RadarIndicatorItem(name='ability2',max_=150),
#             opts.RadarIndicatorItem(name='ability3',max_=150),
#             opts.RadarIndicatorItem(name='ability4',max_=100),
#             opts.RadarIndicatorItem(name='ability5',max_=100),
#             opts.RadarIndicatorItem(name='ability6',max_=100),
#         ]
#     )
#     .add('budget',v1)# 添加一条数据，参数1为数据名，参数2为数据
#     .add('fact',v2) # schema有几个indicator指示器就会默认取前几个数值
#     # .set_global_opts(title_opts=opts.TitleOpts(title='radar 基本示例'),)
# )
# print(radar1.render_embed('template.html'))
# todo https://programmersought.com/article/16462935862/


# from snapshot_selenium import snapshot as driver
#
# from pyecharts import options as opts
# from pyecharts.charts import Bar
# from pyecharts.render import make_snapshot
#
#
# def bar_chart() -> Bar:
#     c = (
#         Bar()
#         .add_xaxis(["衬衫", "毛衣", "领带", "裤子", "风衣", "高跟鞋", "袜子"])
#         .add_yaxis("商家A", [114, 55, 27, 101, 125, 27, 105])
#         .add_yaxis("商家B", [57, 134, 137, 129, 145, 60, 49])
#         .reversal_axis()
#         .set_series_opts(label_opts=opts.LabelOpts(position="right"))
#         .set_global_opts(title_opts=opts.TitleOpts(title="Bar-测试渲染图片"))
#     )
#     return c
#
# # 需要安装 snapshot-selenium 或者 snapshot-phantomjs
# make_snapshot(driver, bar_chart().render(), "bar.png")

from pyecharts.charts import Bar
from pyecharts import options as opts

from pyecharts.globals import CurrentConfig

# # V1 版本开始支持链式调用
# bar = (
#     Bar()
#     .add_xaxis(["衬衫", "毛衣", "领带", "裤子", "风衣", "高跟鞋", "袜子"])
#     .add_yaxis("商家A", [114, 55, 27, 101, 125, 27, 105])
#     .add_yaxis("商家B", [57, 134, 137, 129, 145, 60, 49])
#     .set_global_opts(title_opts=opts.TitleOpts(title="某商场销售情况"))
# )
# bar.render()

# 不习惯链式调用的开发者依旧可以单独调用方法
# bar = Bar()
# bar.add_xaxis(["衬衫", "毛衣", "领带", "裤子", "风衣", "高跟鞋", "袜子"])
# bar.add_yaxis("商家A", [114, 55, 27, 101, 125, 27, 105])
# bar.add_yaxis("商家B", [57, 134, 137, 129, 145, 60, 49])
# bar.set_global_opts(title_opts=opts.TitleOpts(title="某商场销售情况"))
#
# # s = os.path.join(
# #                  os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "templates"
# #              )
#
# env = Environment(
#         keep_trailing_newline=True,
#         trim_blocks=True,
#         lstrip_blocks=True,
#         loader=FileSystemLoader(
#             (
#                 os.path.join(os.path.dirname(__file__), "templates")
#             )
#         )
#     )
#
# print(bar.render_embed('template.html', env))

# from pyecharts import options as opts
# from pyecharts.charts import Pie
from pyecharts.faker import Faker
#
# list = [list(z) for z in zip(Faker.choose(), Faker.values())]
#
# c = (
#     Pie()
#     .add("", list)
#     .set_global_opts(title_opts=opts.TitleOpts(title="Pie-基本示例"))
#     .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
#     .render("pie_base.html")
# )
#
# filename = 'file:///' + os.getcwd() + '/' + 'pie_base.html'
#
# webbrowser.open_new_tab(filename)


import pyecharts.options as opts
from pyecharts.charts import Scatter

# """
# Gallery 使用 pyecharts 1.1.0
# 参考地址: https://echarts.apache.org/examples/editor.html?c=scatter-simple
# 目前无法实现的功能:
# 1、暂无
# """
#
# data = [
#     [10.0, 8.04],
#     [8.0, 6.95],
#     [13.0, 7.58],
#     [9.0, 8.81],
#     [11.0, 8.33],
#     [14.0, 9.96],
#     [6.0, 7.24],
#     [4.0, 4.26],
#     [12.0, 10.84],
#     [7.0, 4.82],
#     [5.0, 5.68],
# ]
# data.sort(key=lambda x: x[0])
# x_data = [d[0] for d in data]
# y_data = [d[1] for d in data]
#
# (
#     Scatter()
#     .add_xaxis(xaxis_data=x_data)
#     .add_yaxis(
#         series_name="aaa",
#         y_axis=y_data,
#         symbol_size=20,
#         label_opts=opts.LabelOpts(is_show=False),
#     )
#     .add_yaxis(
#         series_name="bbb",
#         y_axis=y_data,
#         symbol_size=10,
#         label_opts=opts.LabelOpts(is_show=False),
#     )
#     .set_series_opts()
#     .set_global_opts(
#         xaxis_opts=opts.AxisOpts(
#             type_="value", splitline_opts=opts.SplitLineOpts(is_show=False)
#         ),
#         yaxis_opts=opts.AxisOpts(
#             type_="value",
#             axistick_opts=opts.AxisTickOpts(is_show=True),
#             splitline_opts=opts.SplitLineOpts(is_show=False),
#         ),
#         tooltip_opts=opts.TooltipOpts(is_show=True),
#     )
#     .render("basic_scatter_chart.html")
# )
# filename = 'file:///' + os.getcwd() + '/' + 'basic_scatter_chart.html'
#
# webbrowser.open_new_tab(filename)

from pyecharts import options as opts
from pyecharts.charts import Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.faker import Faker

# choose = Faker.values()
# c = (
#     Scatter()
#     .add_xaxis(choose)
#     .add_yaxis(
#         "Lab A",
#         # [list(z) for z in zip(choose, Faker.values())],
#         Faker.values(),
#         label_opts=opts.LabelOpts(
#             formatter=JsCode(
#                 "function(params){return params.value[1] +' : '+ params.value[2];}"
#             )
#         ),
#     )
#     .add_yaxis(
#             "Lab B",
#             # [list(z) for z in zip(choose, Faker.values())],
#             Faker.values(),
#             label_opts=opts.LabelOpts(
#                 formatter=JsCode(
#                     "function(params){return params.value[1] +' : '+ params.value[2];}"
#                 )
#             ),
#         )
#     .set_global_opts(
#         title_opts=opts.TitleOpts(title="Scatter-Scatter_multi_dimension"),
#         tooltip_opts=opts.TooltipOpts(
#             formatter=JsCode(
#                 "function (params) {return params.name + ' : ' + params.value[2];}"
#             )
#         ),
#         visualmap_opts=opts.VisualMapOpts(
#             type_="color", max_=150, min_=20, dimension=1
#         ),
#         xaxis_opts={
#                     'data': None,
#                     'type': 'value',
#                     'scale': True,
#                     "splitLine": {
#                         "show": False,
#                     }
#                 },
#         yaxis_opts={
#                     # 'data': None,
#                     'type': 'value',
#                     'scale': True,
#                     "splitLine": {
#                         "show": False,
#                     }
#                 },
#     )
#     .set_series_opts(emphasis={
#                 'focus': 'series'
#             })
#     .render("scatter_multi_dimension.html")
# )

# 例5 多维度+自定义数据
# scatter5=(
#     Scatter()
#         .add_xaxis(Faker.choose())
#         .add_yaxis(
#         "商家A",
#         [list(z) for z in zip(Faker.values(), Faker.choose())],
#         label_opts=opts.LabelOpts(
#             formatter=JsCode(# 调用js代码设置方法提取参数第2个值和参数第3个值
#                 "function(params){return params.value[1] +' : '+ params.value[2];}"
#             )
#         ),
#     )
#         .set_global_opts(
#         title_opts=opts.TitleOpts(title="例5 Scatter-多维度数据"),
#         tooltip_opts=opts.TooltipOpts(# tooltip是鼠标移上去的提示
#             formatter=JsCode(# 调用js代码设置方法提取参数名字和参数第3个值
#                 "function (params) {return params.name + ' : ' + params.value[2];}"
#             )
#         ),
#         visualmap_opts=opts.VisualMapOpts(
#              max_=150, min_=20, dimension=1
#             # dimension设置维度为1维
#         ),
#     )
# )
# scatter5.render('echarts-scatter.html')
# filename = 'file:///' + os.getcwd() + '/' + 'echarts-scatter.html'
# from pyecharts import options as opts
# from pyecharts.charts import Bar
# from pyecharts.faker import Faker
#
# c = (
#     Bar()
#     .add_xaxis(Faker.choose())
#     .add_yaxis("商家A", Faker.values())
#     .add_yaxis("商家B", Faker.values())
#     .extend_axis(
#         yaxis=opts.AxisOpts(
#             is_inverse=True,
#
#         ),
#         xaxis=opts.AxisOpts(
#             is_inverse=True
#         )
#     )
#     # .reversal_axis()
#     .set_series_opts(
#         label_opts=opts.LabelOpts(position="right"),
#
#     )
#     .set_global_opts(
#         title_opts=opts.TitleOpts(title="Bar-翻转 XY 轴"),
#         xaxis_opts=opts.AxisOpts(
#             position='top'
#         ),
#         yaxis_opts=opts.AxisOpts(
#             position='right'
#         )
#     )
#     .render("bar_reversal_axis.html")
# )
#
# filename = 'file:///' + os.getcwd() + '/' + 'bar_reversal_axis.html'
# webbrowser.open_new_tab(filename)
# import re
#
# string = "当前指数：1622.084↓    -1.900    -0.120%    成交额 572.80亿元    " \
#          "平均价格 127.859    转股溢价率 31.22%    到期收益率 -0.88%    中位数价格 111.110    换手率 9.84%"
# # print(re.findall(r"\d+\.?\d*", string))
# print(re.findall(r"转股溢价率 (\d+\.?\d*)%", string))
# # re.findall(r"中位数价格 \d+\.?\d*", string)
# print(re.findall(r"到期收益率 (-?\d+\.?\d*)%", string))

# import pinyin
# print(pinyin.get('建工转债'))

from pytz import unicode

# 获取汉字首字母
def multi_get_letter(str_input):
	if isinstance(str_input, unicode):
		unicode_str = str_input
	else:
		try:
			unicode_str = str_input.decode('utf8')
		except:
			try:
				unicode_str = str_input.decode('gbk')
			except:
				print('unknown coding')
				return
	return_list = []
	for one_unicode in unicode_str:
		return_list.append(single_get_first(one_unicode))
	return return_list

def single_get_first(unicode1):
	str1 = unicode1.encode('gbk')
	# print(len(str1))
	try:
		ord(str1)
		return str1
	except:
		asc = str1[0] * 256 + str1[1] - 65536
		# print(asc)
		if asc >= -20319 and asc <= -20284:
			return 'a'
		if asc >= -20283 and asc <= -19776:
			return 'b'
		if asc >= -19775 and asc <= -19219:
			return 'c'
		if asc >= -19218 and asc <= -18711:
			return 'd'
		if asc >= -18710 and asc <= -18527:
			return 'e'
		if asc >= -18526 and asc <= -18240:
			return 'f'
		if asc >= -18239 and asc <= -17923:
			return 'g'
		if asc >= -17922 and asc <= -17418:
			return 'h'
		if asc >= -17417 and asc <= -16475:
			return 'j'
		if asc >= -16474 and asc <= -16213:
			return 'k'
		if asc >= -16212 and asc <= -15641:
			return 'l'
		if asc >= -15640 and asc <= -15166:
			return 'm'
		if asc >= -15165 and asc <= -14923:
			return 'n'
		if asc >= -14922 and asc <= -14915:
			return 'o'
		if asc >= -14914 and asc <= -14631:
			return 'p'
		if asc >= -14630 and asc <= -14150:
			return 'q'
		if asc >= -14149 and asc <= -14091:
			return 'r'
		if asc >= -14090 and asc <= -13119:
			return 's'
		if asc >= -13118 and asc <= -12839:
			return 't'
		if asc >= -12838 and asc <= -12557:
			return 'w'
		if asc >= -12556 and asc <= -11848:
			return 'x'
		if asc >= -11847 and asc <= -11056:
			return 'y'
		if asc >= -11055 and asc <= -10247:
			return 'z'
		return ''

def main(str_input):
    list1 = multi_get_letter(str_input)
    res = ''
    for i in list1:
        if type(i).__name__ == 'bytes':
            i = i.decode()
        res = res + i
    print(res)
if __name__ == "__main__":
	str_input='世界欢迎你'
	main(str_input)
