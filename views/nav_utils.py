analysis_nav_html_dict = {
    '/': (1, '<li><a href="/">Home</a></li>'),
    '/view_tree_map_industry.html': (2, '<li><a href="/view_tree_map_industry.html">可转债涨跌行业分布</a></li>'),
    '/view_tree_map_price.html': (3, '<li><a href="/view_tree_map_price.html">涨跌价格分布</a></li>'),
    '/view_tree_map_premium.html': (4, '<li><a href="/view_tree_map_premium.html">涨跌溢价率分布</a></li>'),
    '/view_up_down_range.html': (5, '<li><a href="/view_up_down_range.html">可转债涨跌幅分布</a></li>'),
    '/view_all_cb.html': (6, '<li><a href="/view_all_cb.html">可转债象限分布</a></li>'),
    '/view_up_down.html': (7, '<li><a href="/view_up_down.html">可转债涨跌排行</a></li>'),
    '/view_discount.html': (8, '<li><a href="/view_discount.html">溢价率折价排行</a></li>'),
    '/view_stock.html': (9, '<li><a href="/view_stock.html">正股涨幅排行</a></li>'),
    '/view_turnover.html': (10, '<li><a href="/view_turnover.html">换手率排行</a></li>'),
}
personal_nav_html_dict = {
    '/': (1, '<li><a href="/">Home</a></li>'),
    '/view_my_account.html': (2, '<li><a href="/view_my_account.html">按账户统计</a></li>'),
    '/view_my_strategy.html': (3, '<li><a href="/view_my_strategy.html">按策略统计</a></li>'),
    '/view_my_up_down.html': (4, '<li><a href="/view_my_up_down.html">可转债涨跌排行</a></li>'),
    '/view_my_price_list.html': (5, '<li><a href="/view_my_price_list.html">可转债价格排行</a></li>'),
    '/view_my_yield.html': (6, '<li><a href="/view_my_yield.html">我的收益率</a></li>'),
    '/view_my_trade_history.html': (6, '<li><a href="/view_my_trade_history.html">我的成交记录</a></li>'),
}
select_nav_html_dict = {
    '/': (1, '<li><a href="/">Home</a></li>'),
    '/view_my_select.html': (2, '<li><a href="/view_my_select.html">自选列表</a></li>'),
    '/edit_changed_bond_select.html': (3, '<li><a href="/edit_changed_bond_select.html">添加自选</a></li>'),
}


def build_select_nav_html(url):
    return to_html(select_nav_html_dict, url)


def build_personal_nav_html_list(url=None):
    return to_list(personal_nav_html_dict, url)


def build_personal_nav_html(url=None):
    return to_html(personal_nav_html_dict, url)


def build_analysis_nav_html(url):
    return to_html(analysis_nav_html_dict, url)


def to_html(nav_dict, url):
    new_list = to_list(nav_dict, url)
    return ''.join(new_list)


def to_list(nav_dict, url=None):
    copy_dict = nav_dict.copy()
    if url is not None:
        copy_dict.pop(url)

    sorted_nav_list = sorted(copy_dict.items(), key=lambda key_value: key_value[1][0])
    new_list = []
    for value in sorted_nav_list:
        new_list.append(value[1][1])
    return new_list