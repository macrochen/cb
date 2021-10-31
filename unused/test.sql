select *
                from (select a.*, case when sort_num is NULL then '调入' else '持有' end as rotate
                      from (select a.*,

                                   (select count(*)
                                    from (select cb_price2_id + cb_premium_id * 100 as sort_value
                                          from changed_bond_view
                                          order by cb_price2_id + cb_premium_id * 100
                                          limit 10) b
                                    where a.sort_value >= b.sort_value) as '当前排序'
                            from (select *
                                  from (select a.*,
                                               date()                                 as create_date,

                                               '双低策略'                                 as strategy_name,
                                               b.sort_num,
                                               a.cb_price2_id + a.cb_premium_id * 100 as sort_value
                                        from (select *
                                              from changed_bond_view
                                              order by cb_price2_id + cb_premium_id * 100
                                              limit 10) a
                                                 left join (select *
                                                            from changed_bond_top_history
                                                            where strategy_name = '双低策略'
                                                            and create_date_s = :create_date_s
                                                            ) b on a.id = b.id) c) a) a
                      UNION
                      select *, '' as '当前排序', '调出' as rotate
                      from (select b.*, b.cb_price2_id + b.cb_premium_id * 100 as sort_value
                            from changed_bond_top_history b
                                     left join (select a.*
                                                from changed_bond_view a
                                                order by a.cb_price2_id + a.cb_premium_id * 100
                                                limit 10) a on b.id = a.id
                            where b.strategy_name = '双低策略'
                              and a.id is NULL
                              and create_date_s = :create_date_s))
                order by cb_price2_id + cb_premium_id * 100