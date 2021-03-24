--活性债
SELECT c.bond_code as 转债编码,  c.cb_name_id as 名称, c.stock_code as 正股代码, c.stock_name as 正股名称, c.industry as 行业, c.sub_industry as 子行业,
cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率,
rating as 信用, duration as 续存期, round(bt_yield*100,2) as 税前收益率,
round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate as '应收同比(%)', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate as '净利润同比(%)', s.margin as '利润率(%)', s.yoy_margin_rate as '利润率同比(%)', s.roe as 'ROE(%)', s.yoy_roe_rate as 'ROE同比(%)', round(s.al_ratio,2) as 负债率, s.yoy_al_ratio_rate as '负债率同比(%)', last_date as 报告期, stock_pb as PB,
market_cap as '股票市值(亿元)', remain_amount as '转股余额(亿元)', round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
--, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
    from changed_bond c, stock_report s
	where c.bond_code = s.bond_code
	and duration < 3
	-- and cb_price2_id > 108
	and cb_price2_id < 120
	and roe > 5
	and s.net > 0
	and s.margin > 10
	and cb_t_id = '转股中'
	-- and 溢价率 < 20
	-- and 双低值 < 120
	order by 双低值 ASC


-- 我持有转债
select * from changed_bond