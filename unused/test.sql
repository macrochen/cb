SELECT DISTINCT d.*, e.hold_id, e.hold_amount as 持有数量
FROM (
         SELECT data_id                                      as nid,
                bond_code,
                stock_code,
                cb_name_id                                   as 名称,
                sort_num,
                cur_sort                                     as 排序,
                rotate                                       as 轮动,
                round(cb_mov2_id * 100, 2) || '%'            as 可转债涨跌,
                cb_price2_id                                 as '转债价格',
                round(cb_premium_id * 100, 2) || '%'         as 溢价率,
                round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
                round(bt_yield * 100, 2) || '%'              as 到期收益率,
                round(cb_mov_id * 100, 2) || '%'             as 正股涨跌,
                stock_name                                   as 正股名称,
                industry                                     as '行业',
                sub_industry                                 as '子行业'
         from (select *
               from (select f.*, case when sort_num is NULL then '轮入' else '持有' end as rotate
                     from (select d.*,
                                  (select count(*)
                                   from (select bt_yield as sort_value
                                         from changed_bond_view
                                         order by cb_price2_id + cb_premium_id * 100
                                         limit 10) e
                                   where d.sort_value >= e.sort_value) as cur_sort
                           from (select c.*
                                 from (select a.*,
                                              date()                                 as create_date,
                                              strftime('%s', date())                 as create_date_s,
                                              ''                                     as strategy_name,
                                              b.sort_num,
                                              a.cb_price2_id + a.cb_premium_id * 100 as sort_value
                                       from (select *
                                             from changed_bond_view
                                             order by cb_price2_id + cb_premium_id * 100
                                             limit 10) a
                                                left join (select *
                                                           from changed_bond_top_history
                                                           where strategy_name = '双低策略'
                                                             and create_date_s = :create_date_s) b on a.id = b.id
                                      ) c) d) f
                     UNION
                     select d.*,
                            ''   as create_date,
                            ''   as create_date_s,
                            ''   as strategy_name,
                            c.sort_num,
                            ''   as sort_value,
                            ''   as cur_sort,
                            '轮出' as rotate
                     from changed_bond_view d
                              inner join (select b.*
                                          from changed_bond_top_history b
                                                   left join (select *
                                                              from changed_bond_view
                                                              order by cb_price2_id + cb_premium_id * 100
                                                              limit 10) a on b.id = a.id
                                          where b.strategy_name = '双低策略'
                                            and a.id is NULL
                                            and create_date_s = :create_date_s) c
                                         on d.id = c.id)
               order by cur_sort, sort_num)
     ) d
         left join
     (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount
      from hold_bond
         --where strategy_type = '双低策略轮动'
     ) e
     on d.bond_code = e.bond_code