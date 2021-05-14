#!/bin/bash
source venv/bin/activate

# 更新数据
python3 cb_ninwen.py

# 生成数据
python3 view_market.py

# 移动到指定位置
mv ./view/view_market.html ./../trader/public/view_market.html