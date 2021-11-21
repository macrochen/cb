select *
from (select *
      from (SELECT cb_name_id,
                   cb_price2_id                               as 价格,
                   cb_price2_id + cb_premium_id * 100 * 1.6   as 双低值,
                   (cb_premium_id * 100) || '%'               as 溢价率,
                   remain_amount                              as 余额,
                   round(cb_trade_amount2_id * 100, 2) || '%' as '换手率(%)'
            from changed_bond
            where cb_price2_id >= 110
              and cb_price2_id <= 130
            order by cb_trade_amount2_id desc
            limit 100)
      order by 双低值
      limit 50)
order by 余额