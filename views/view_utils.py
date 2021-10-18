def add_popwin_js_code(chart, chart_id):
    chart.add_js_funcs(
        'chart_' + chart_id + """.on('click', function(params){
            // alert(params)
            popWin.showWin("1200","600", params['data']['bond_code']);
        })
    """)