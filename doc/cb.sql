--活性债 top n
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
	order by 双低值 ASC;

-- 双低 top n
SELECT round(cb_price2_id + cb_premium_id * 100, 2) as 双低值 ,  c.bond_code as 转债编码,  c.cb_name_id as 名称, c.stock_code as 正股代码, c.stock_name as 正股名称, c.industry as 行业, c.sub_industry as 子行业,
cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率,
rating as 信用, duration as 续存期, round(bt_yield*100,2) as 税前收益率,
market_cap as '股票市值(亿元)', remain_amount as '转股余额(亿元)', round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
red_t as 回售年限, round(bt_red * 100,2) as '税前回售价值',
cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
 from changed_bond c
where red_t not in ('回售内')
 order  by 双低值 ASC limit 25;

--低价格高收益 top n
SELECT cb_num_id, cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, bt_yield*100 as 收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比
    from changed_bond cb
    WHERE
    cb.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+')
    -- cb_name_id not in( '亚药转债' , '本钢转债','搜特转债','广汇转债')
    AND bt_yield > -0
    and cb_price2_id < 110
    order by 转债价格 ASC, 收益率 DESC
    limit  30;

--回售 top n
SELECT cb.cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, bt_red * 100 as 回售收益率, red_t as 回售年限, duration as 续存期, bond_t1 as 剩余年限, round((bt_red * 100) + (2-bond_t1),2) as 性价比
from changed_bond cb
WHERE 回售年限 not in('无权', '回售内')
and 回售年限 < 1.5
and 回售收益率 > 1
--ORDER by 回售年限 ASC, 回售收益率 DESC;
ORDER by 性价比 DESC;

-- 我的低价格高收益
SELECT cb.cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, bt_yield * 100 as 税前收益率
from changed_bond cb, hold_bond h
WHERE cb.bond_code = h.bond_code AND h.strategy_type = '低价格高收益'
ORDER by 税前收益率;

-- 我的回售
SELECT cb.cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, bt_red * 100 as 税前回售收益率, red_t as 回售年限
from changed_bond cb, hold_bond h
WHERE cb.bond_code = h.bond_code AND h.strategy_type = '回售'
order by 税前回售收益率;

-- 我持有转债基本面分析
select c.bond_code as 转债编码,  c.cb_name_id as 名称, c.stock_code as 正股代码, c.stock_name as 正股名称, c.industry as 行业, c.sub_industry as 子行业,
cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率,
rating as 信用, duration as 续存期, round(bt_yield*100,2) as 税前收益率,
round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate as '应收同比(%)', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate as '净利润同比(%)', s.margin as '利润率(%)', s.yoy_margin_rate as '利润率同比(%)', s.roe as 'ROE(%)', s.yoy_roe_rate as 'ROE同比(%)', round(s.al_ratio,2) as 负债率, s.yoy_al_ratio_rate as '负债率同比(%)', last_date as 报告期, stock_pb as PB,
market_cap as '股票市值(亿元)', remain_amount as '转股余额(亿元)', round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
from changed_bond c, stock_report s, hold_bond h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code
