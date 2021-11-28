select a.bond_id,
       a.last_chg_dt,
       a.price,
       a.premium_rt,
       a.is_enforce,
       b.price                                       as pre_7_price,
       round((a.price - b.price) / b.price * 100, 0) as rise_rate
from cb_history a
         left join (select *
                    from cb_history
                    where last_chg_dt =
                          (select max(distinct (last_chg_dt)) from cb_history where last_chg_dt <= '2012-12-23')) b
                   on a.bond_id = b.bond_id
where a.bond_id in
      (110007, 110012, 110015, 110016, 110018, 110019, 110020, 110022, 113001, 113002, 113003, 125089, 125731, 126729,
       129031)
  and a.last_chg_dt = '2012-12-24';


select a.bond_id,
       a.last_chg_dt,
       a.price,
       a.premium_rt,
       a.is_enforce
from cb_history a

where a.last_chg_dt = '2012-12-24'