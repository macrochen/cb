def is_too_expensive(rows, group=None, max_double_low=150):
    low_150_count = 0
    total_num = 0
    # group的数据最全最新, 优先用group判断
    if group is not None:
        total_num = len(group.values())
        for bond in group.values():
            if (bond['price'] + bond['premium'] * 100) < max_double_low:
                low_150_count += 1
    else:
        total_num = len(rows)
        for row in rows:
            bond_id = row[0]
            price = row[2]
            premium = row[3]
            if price is None and group is not None:
                bond = group.get(bond_id)
                price = bond.get("price")
                premium = bond.get("premium")

            if price + premium * 100 < max_double_low:
                low_150_count += 1

    # 双低值小于150的数量是否小于等于2/3
    expensive = low_150_count < round(total_num * 2 / 3, 0)
    if expensive and group is not None:
        print("it's too expensive to sell all bonds: " + str(rows))
        group.clear()

    return expensive


def parse_bond_ids_params(bond_ids, params):
    ids = ""
    first = True
    i = 0
    for bond_id in bond_ids:
        i += 1
        if first:
            first = False
        else:
            ids += ','
        ids += ':id_' + str(i)
        params.setdefault("id_" + str(i), bond_id)
    return ids