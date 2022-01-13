analysis_nav_html_list = [
    '<li><a href="/">Home</a></li>',
    '<li class=\'$active\'><a href="/view_tree_map_industry.html">行业涨跌分布</a></li>',
    '<li class=\'$active\'><a href="/view_industry_premium.html">行业价格&溢价率分布</a></li>',
    '<li class=\'$active\'><a href="/view_industry_double_low.html">行业双低值分布</a></li>',
    '<li class=\'$active\'><a href="/view_tree_map_price.html">价格涨跌分布</a></li>',
    '<li class=\'$active\'><a href="/view_tree_map_remain.html">余额分布</a></li>',
    '<li class=\'$active\'><a href="/view_tree_map_premium.html">溢价率分布</a></li>',
    '<li class=\'$active\'><a href="/view_up_down_range.html">涨跌幅分布</a></li>',
    '<li class=\'$active\'><a href="/view_price_range.html">价格范围分布</a></li>',
    '<li class=\'$active\'><a href="/view_all_cb.html">全市场可转债分布</a></li>',
    '<li class=\'$active\'><a href="/view_cb_wordcloud.html">可转债概念分析</a></li>',
    '<li class=\'$active\'><a href="/view_hot_wordcloud.html">可转债热度分析</a></li>',
    '<li class=\'$active\'><a href="/view_up_down.html">涨跌排行</a></li>',
    '<li class=\'$active\'><a href="/view_discount.html">溢价率折价排行</a></li>',
    '<li class=\'$active\'><a href="/view_stock.html">正股涨幅排行</a></li>',
    '<li class=\'$active\'><a href="/view_turnover.html">换手率排行</a></li>',
]
back_test_nav_html_list = [
    '<li><a href="/">Home</a></li>',
    # '<li class=\'$active\'><a href="/view_custom_back_test.html">定制化回测</a></li>',
    '<li class=\'$active\'><a href="/view_good_year_back_test.html">行情好时的回测</a></li>',
    '<li class=\'$active\'><a href="/view_bad_year_back_test.html">行情差时的回测</a></li>',
    '<li class=\'$active\'><a href="/view_long_year_back_test.html">长周期下的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_1.html">低溢价策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_2.html">低余额+低溢价+双低策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_3.html">低余额+双低策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_4.html">低溢价+双低策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_5.html">双低策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_8.html">三低策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_6.html">高溢价策略的回测</a></li>',
    '<li class=\'$active\'><a href="/view_back_test_7.html">低价格策略的回测</a></li>',
]
personal_nav_html_list = [
    '<li><a href="/">Home</a></li>',
    '<li class=\'$active\'><a href="/view_my_account.html">按账户统计</a></li>',
    '<li class=\'$active\'><a href="/view_my_strategy.html">按策略统计</a></li>',
    '<li class=\'$active\'><a href="/new_sync_trade_data.html">同步交易数据</a></li>',
    '<li class=\'$active\'><a href="/view_my_up_down.html">可转债涨跌排行</a></li>',
    '<li class=\'$active\'><a href="/view_my_price_list.html">可转债价格排行</a></li>',
    '<li class=\'$active\'><a href="/view_my_yield.html">我的收益率</a></li>',
    '<li class=\'$active\'><a href="/view_my_trade_history.html">我的成交记录</a></li>',
]
select_nav_html_list = [
    '<li><a href="/">Home</a></li>',
    '<li class=\'$active\'><a href="/view_my_select.html">自选列表</a></li>',
    '<li class=\'$active\'><a href="/edit_changed_bond_select.html">添加自选</a></li>',
]


def build_select_nav_html(url):
    new_list = []
    for li in select_nav_html_list:
        if str(url) in li:
            new_list.append(li.replace('$active', 'active'))
        else:
            new_list.append(li.replace('$active', ''))
    return ''.join(new_list)


def build_personal_nav_html_list():
    return personal_nav_html_list.copy()


def build_personal_nav_html(url, nav_list=personal_nav_html_list):
    new_list = []
    for li in nav_list:
        if str(url) in li:
            new_list.append(li.replace('$active', 'active'))
        else:
            new_list.append(li.replace('$active', ''))
    return ''.join(new_list)


def build_analysis_nav_html(url):
    new_list = []
    for li in analysis_nav_html_list:
        if str(url) in li:
            new_list.append(li.replace('$active', 'active'))
        else:
            new_list.append(li.replace('$active', ''))
    return ''.join(new_list)


def build_back_test_nav_html(url):
    new_list = []
    for li in back_test_nav_html_list:
        if str(url) in li:
            new_list.append(li.replace('$active', 'active'))
        else:
            new_list.append(li.replace('$active', ''))
    return ''.join(new_list)
