select a.industry, round(b.涨跌幅 / a.个数 * 100, 2) as 涨跌, 余额
from (SELECT industry, count(industry) as 个数 from changed_bond group by industry) a,
     (SELECT industry, sum(cb_mov2_id) as 涨跌幅 from changed_bond group by industry) b,
     (SELECT industry, round(sum(remain_amount), 2) as 余额 from changed_bond group by industry) c
where a.industry = b.industry
  and a.industry = c.industry
order by 涨跌 desc