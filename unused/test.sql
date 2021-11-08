insert into changed_bond_top_history
select c.*,
       date()   as create_date,
       '高收益率策略' as strategy_name,
       d.sort_num
from changed_bond c,
     (select id,
             (select count(*)
              from (select BT_yield, cb_price2_id
                    from changed_bond_view
                    order by BT_yield desc, cb_price2_id
                    limit 10) b
              where case
                        when a.BT_yield < b.BT_yield then true
                        when a.BT_yield = b.BT_yield then a.cb_price2_id > b.cb_price2_id
                        else false end) as sort_num
      from (select id, BT_yield, cb_price2_id
            from changed_bond_view
            order by BT_yield desc, cb_price2_id
            limit 10) a) d
where c.id = d.id
order by d.sort_num
limit 10