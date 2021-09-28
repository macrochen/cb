

def calc_trade_fee(account, is_sh_market, trade_num):
    fee = 0
    if account == '银河':
        if is_sh_market:  # 沪市百万分之5
            fee = trade_num * 0.000005
        else:  # 沪市十万分之5
            fee = trade_num * 0.00005
    else:
        if is_sh_market:  # 沪市百万分之5
            fee = trade_num * 0.000005
        else:  # 沪市十万分之8
            fee = trade_num * 0.00008
        # 不足0.5按0.5收
        if fee < 0.5:
            fee = 0.5
    fee = round(fee, 2)
    return fee
