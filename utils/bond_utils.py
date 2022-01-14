def is_too_expensive(rows, group=None, max_double_low=150, current_day=None, test_result=None, need_roll_row=False):
    low_count = 0
    # group的数据最全最新, 优先用group判断
    if group is not None:
        total_num = len(group.values())
        for bond in group.values():
            if (bond['price'] + bond['premium'] * 100) < max_double_low:
                low_count += 1
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
                low_count += 1

    # 双低值小于150的数量是否小于等于2/3
    expensive = low_count < round(total_num * 2 / 3, 0)
    if expensive and group is not None:
        print("it's too expensive to sell all bonds: " + str(rows))
        update_test_result(test_result, current_day, group, rows, need_roll_row)

        group.clear()

    return expensive


def update_test_result(test_result, current_day, group, rows, need_roll_row):
    if need_roll_row is False \
            or current_day is None \
            or test_result is None \
            or rows is None:
        return

    for bond_id, bond in group.items():
        new_price = None
        for row in rows:
            if bond_id == row[0]:
                new_price = row[2]
                break
        if new_price is not None:
            add_roll_row_with_bond(test_result, current_day, bond_id, bond, '高估清仓')
        else:
            print('not get price at rows' + str(rows) + ' for bond_id:' + str(bond_id))


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


def add_roll_row_with_bond(test_result, current_day, bond_id, bond, desc, old_bond=None):
    bond_name = bond['bond_nm']
    price = bond['price']
    amount = bond['amount']
    percent = bond['percent']
    premium = round(bond['premium'] * 100, 2)

    _bond = old_bond if old_bond is not None else bond
    if old_bond is not None:
        old_price = old_bond['old_price']
        old_amount = old_bond['amount']
        old_percent = old_bond['old_percent']
        old_premium = round(old_bond['old_premium'] * 100, 2)
    else:
        old_price = bond['old_price']
        old_amount = bond['amount']
        old_percent = bond['old_percent']
        old_premium = round(bond['old_premium'] * 100, 2)

    roll_row = {'bond_id': bond_id,
                'bond_name': bond_name,
                'old_price': old_price,
                'price': price,
                'old_premium': old_premium,
                'premium': premium,
                'old_amount': old_amount,
                'amount': amount,
                'old_percent': old_percent,
                'percent': percent,
                'desc': desc,
                }
    if test_result['roll_rows'].get(current_day) is None:
        test_result['roll_rows'].setdefault(current_day, [{'bond_id': '',
                'bond_name': '',
                'old_price': '',
                'price': '',
                'old_premium': '',
                'premium': '',
                'old_amount': '',
                'amount': '',
                'old_percent': '',
                'percent': '',
                'desc': '',
                }])

    test_result['roll_rows'][current_day].append(roll_row)
