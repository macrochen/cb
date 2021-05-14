# 从网易财经抓取数据
import time

import requests
import bs4
import html5lib
from lxml import etree
import sqlite3

userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"
header = {
    # "origin": "https://xueqiu.com",
    # "Referer": "https://xueqiu.com/snowman/S/SH603098/detail",
    'User-Agent': userAgent,
    # 'Cookie': "PHPSESSID=98a239682d42b69f8d496979abec3dd0; other_uid=Ths_iwencai_Xuangu_ih5kxk7dxi9mx69s63wcords6ayjbvq3; cid=98a239682d42b69f8d496979abec3dd01616046221; ComputerID=98a239682d42b69f8d496979abec3dd01616046221; WafStatus=0; v=A1LeQ6mIZr6HSppCc7SNGxaJpRM3Y1Y2iGZKDByvfy7xL_wFBPOmDVj3mlPv"
}

def createDb():

    con = sqlite3.connect("../db/cb.db3")
    # 只执行一次
    con.executescript("""
        drop table if exists stock_report;
        create table if not exists stock_report(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_code text NOT NULL, 
            cb_name_id text NOT NULL,
            
            stock_code text NOT NULL,
            stock_name text NOT NULL,
            
            last_date text NOT NULL,
            
            revenue real,
            qoq_revenue_rate real,
            yoy_revenue_rate real,
            
            net real,
            qoq_net_rate real,
            yoy_net_rate real,
            
            margin real,
            qoq_margin_rate real,
            yoy_margin_rate real,
            
            roe real,
            qoq_roe_rate real,
            yoy_roe_rate real,
            
            al_ratio real,
            qoq_rl_ratio_rate real,
            yoy_al_ratio_rate real
            
            )""")

    con.commit()
    con.close()
    print("create db is successful")

def getContent():
    # test data
    s = """
    <!DOCTYPE html>
<html>
<head>
<title>鸿达兴业（002002）主要财务指标_股票F10_网易财经</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="keywords" content="鸿达兴业,002002,股票F10,鸿达兴业主要财务指标,鸿达兴业财务报表" />
<meta name="description" content="提供鸿达兴业(002002)股票的股票F10数据、财务指标、财务数据、财务报表等信息。" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Language" content="zh-CN" />
<meta name="robots" content="index, follow" />
<meta name="googlebot" content="index, follow" />
<link href="http://img1.cache.netease.com/f2e/finance/gegu/s.1064000.css" rel="stylesheet" type="text/css" charset="utf-8">
<link href="http://img1.cache.netease.com/f2e/finance/gegu/danmaku.959699.css" rel="stylesheet" type="text/css" charset="utf-8">
</head>
<body class="test">
<script charset="gb2312" src="http://img1.cache.netease.com/cnews/js/ntes_jslib_1.x.js" language="javascript" type="text/javascript"></script>
<div class="NTES_bg_">
  <div class="NTES-nav"> <span class="nav-link"><a href="http://www.163.com/">网易首页</a>-<a href="http://news.163.com/">新闻</a>-<a href="http://sports.163.com/">体育</a>-<a href="http://sports.163.com/nba/">NBA</a>-<a href="http://ent.163.com/">娱乐</a>-<a href="http://money.163.com/">财经</a>-<a href="http://money.163.com/stock/">股票</a>-<a href="http://auto.163.com/" id="_link_auto">汽车</a>-<a href="http://tech.163.com/">科技</a>-<a href="http://mobile.163.com/">手机</a>-<a href="http://lady.163.com/">女人</a>-<a href="http://bbs.163.com/">论坛</a>-<a href="http://v.163.com/">视频</a>-<a href="http://blog.163.com/">博客</a>-<a href="http://house.163.com/" id="houseUrl">房产</a>-<a id="homeUrl" href="http://home.163.com/">家居</a>-<a href="http://edu.163.com/">教育</a>-<a href="http://book.163.com/">读书</a>-<a href="http://game.163.com/" id="_link_game">游戏</a>-<a href="http://t.163.com/">微博</a> |</span>
    <div class="rightCon">
      <div class="NTES-link"> <a href="http://email.163.com/" class="cBlue">免费邮箱</a> - <a href="http://reg.163.com/" class="cBlue">通行证登录</a> </div>
      <a href="http://www.163.com/rss"><img width="26" height="14" border="0" src="http://img3.cache.netease.com/cnews/img07/rss.gif" class="rss" alt="Rss"></a> </div>
  </div>
</div>
<script>
//<![CDATA[
NTES.ready(function($) {
    var P_INFO = NTES.cookie.get("P_INFO");
    var S_INFO = NTES.cookie.get("S_INFO");
    if (P_INFO) {
        var mailconfig = {
            "163.com": "http://entry.mail.163.com/coremail/fcg/ntesdoor2?verifycookie=1&lightweight=1",
            "126.com": "http://entry.mail.126.com/cgi/ntesdoor?verifycookie=1&lightweight=1&style=-1",
            "vip.126.com": "http://reg.vip.126.com/enterMail.m",
            "yeah.net": "http://entry.yeah.net/cgi/ntesdoor?verifycookie=1&lightweight=1&style=-1",
            "188": "http://reg.mail.188.com/servlet/enter",
            "vip.163.com": "http://reg.vip.163.com/enterMail.m?enterVip=true-----------"
        };
        var passport = P_INFO.substr(0, P_INFO.indexOf("|"));
        var username = passport.substr(0, P_INFO.indexOf("@"));
        var logstate = P_INFO.split("|")[2];
        var logiframe = "";
        var pspt = passport.length >= 6 ? passport.substr(0, 5) + "...": passport;
        /@([^*]+)/.test(passport);
        var logdomain = RegExp.$1;
        if (P_INFO && S_INFO || logstate == "1") {
            var entrylink_html = '<a href=\"http://reg.163.com/Main.jsp?username=' + passport + '\">进入通行证</a>';
            if (mailconfig[logdomain] != undefined) {
                entrylink_html += '<a href=\"' + mailconfig[logdomain] + '\">进入我的邮箱</a>'
            }
            if (logdomain == "popo.163.com" || mailconfig[logdomain] != undefined) {
                entrylink_html += '<a href="http://blog.163.com/passportIn.do?entry=163">进入我的博客</a><a href="http://photo.163.com/?username=' + passport + '\">进入我的相册</a>'
            }
            entrylink_html += '<a href="http://yuehui.163.com/">进入我的约会</a><a href="http://t.163.com">进入我的微博</a>';
            if (logdomain == "163.com" || logdomain == "126.com" || logdomain == "yeah.net") {
                logiframe = '<iframe allowTransparency=\"true\" style=\"width: 56px; height:26px; float:left; vertical-align: middle;\" id=\"ifrmNtesMailInfo\" border=\"0\" src=\"http://p.mail.' + logdomain + '/mailinfo/shownewmsg_www_1222.htm\" frameBorder=\"0\" scrolling=\"no\"></iframe>'
            }
            var login_html = '<div class=\"ntes-usercenter\"><div class=\"ntes-usercenter-logined\"><strong id=\"ntes_usercenter_name\" class=\"ntes-usercenter-name\" title=\"欢迎你，' + passport + '\">' + pspt + '</strong></div><div id=\"ntes_usercenter_entry\" class=\"ntes-usercenter-entry\"><span class=\"user-entry\">' + entrylink_html + '</span></div></div>' + logiframe + '|<a class=\"ntes-usercenter-loginout\" href=\"http://reg.163.com/Logout.jsp?username=' + passport + '\" target=\"_self\">退出</a></div>';
            $(".NTES-link")[0].innerHTML = login_html;
            $("#ntes_usercenter_name").addEvent("click",
            function(e) {
                $("#ntes_usercenter_entry").style.display = $("#ntes_usercenter_entry").style.display == "block" ? "none": "block";
                e.preventDefault();
                e.cancelBubble = true;
                document.onclick = function() {
                    $("#ntes_usercenter_entry").style.display = "none"
                }
            })
        }
    }
})
//]]>
</script>

<div class="area">
    <div class="header">
    <div class="logo_area">
        <a href="http://money.163.com" class="logo" title="网易财经"></a><span
        class="title">个股行情</span>
        <span class="crumbs"><a href="http://www.163.com">网易首页</a><span>&gt;</span><a
            href="http://money.163.com">网易财经</a><span>&gt;</span><a
            href="http://quotes.money.163.com">行情</a><span>&gt;</span><a
            href="http://quotes.money.163.com">沪深</a><span>&gt;</span><a
            href="/1002002.html">鸿达兴业</a><span>&gt;</span><a
                    href="#">主要财务指标</a>
                        </span>
        <iframe src="http://money.163.com/special/ad224_30/" frameborder="0" scrolling="no" style="width:245px;height:40px;border:none;margin-top:-20px;vertical-align: middle;"></iframe>
    </div>
    <table class="main_nav">
        <tr>
            <td><a href="http://quotes.money.163.com/" title="行情中心" target="_blank">行情中心</a></td>
            <!--<td><a href="" title="数据中心">数据中心</a></td>
            <td><a href="" title="资金流向">资金流向</a></td>-->
            <!--<td><a href="http://i.money.163.com/" title="我的投资" class="separate" target="_blank">我的投资</a></td>-->
            <td><a href="http://money.163.com/stock" title="股票" target="_blank">股票</a></td>
            <td><a href="http://money.163.com/ipo" title="新股" target="_blank">新股</a></td>
            <td><a href="http://money.163.com/kechuangban/" title="科创板" target="_blank">科创板</a></td>
            <!--<td><a href="http://money.163.com/chinext" title="创业板" target="_blank">创业板</a></td>-->
            <td><a href="http://money.163.com/fund" title="基金" target="_blank">基金</a></td>
            <td><a href="http://money.163.com/hkstock" title="港股" target="_blank">港股</a></td>
            <td><a href="http://money.163.com/usstock" title="美股" target="_blank">美股</a></td>
            <td><a href="http://money.163.com/special/qhzx/" title="期货" target="_blank">期货</a></td>
            <td><a href="http://money.163.com/forex/" title="外汇" target="_blank">外汇</a></td>
        </tr>
    </table>
    <div class="top_info clearfix">
        <div class="col_1">
            <span><a class="fB" href="http://quotes.money.163.com/0000001.html" target="_blank">上证指数</a></span>
            <span _ntesquote_="code:0000001;attr:price;fixed:2;color:updown;bgchg:price"></span>
            <span _ntesquote_="code:0000001;attr:updown;fixed:2;color:updown;"></span>
            <span _ntesquote_="code:0000001;attr:percent;percent:2;color:updown;"></span>
            <span><em _ntesquote_="code:0000001;attr:turnover;fixed:0;/:100000000"></em>亿</span>
        </div>
        <div class="col_2 separate">
            <div class="mystock">
                <a href="http://i.money.163.com" target="_blank" id="mystock" class="top_mystock"></a>
            </div>
        </div>
        <div class="col_3">
            <input type="button" class="button" value="搜索" id="stockSearchBtn"><input id="stockSearch" name="stock_search" autocomplete="off" type="text" class="field"  placeholder="代码/拼音/名称">
        </div>
    </div>
    <div class="stock_info">
	<table>
		<tr>
			<td class="col_1">
			    <h1 class="name">
					<a href='/1002002.html'>鸿达兴业</a>
					<span>(<a href='/1002002.html'>002002</a>)</span>
			    </h1>
			</td>
			<td class="col_2">
				<div  class="stock_detail">
					<table>
						<tr>
							<td class="price">							<span _ntesquote_="code:1002002;fmt:pic_updown;" class="price_arrow"><strong _ntesquote_="code:1002002;attr:price;fixed:2;color:updown"></strong></span><em _ntesquote_="code:1002002;attr:updown;fixed:2;color:updown"></em><br /><em _ntesquote_="code:1002002;attr:percent;percent:2;color:updown"></em>
							</td>
							<td>今开：<strong _ntesquote_="code:1002002;attr:open;fixed:2;color:updown"></strong><br />昨收：<strong _ntesquote_="code:1002002;attr:yestclose;fixed:2;color:updown"></strong></td>
							<td>最高：<strong _ntesquote_="code:1002002;attr:high;fixed:2;color:updown"></strong><br />最低：<strong _ntesquote_="code:1002002;attr:low;fixed:2;color:updown"></strong></td>
							<td>成交量：<strong _ntesquote_="code:1002002;attr:volume;fmt:volume-cut"></strong><br />成交额：<strong _ntesquote_="code:1002002;attr:turnover;fmt:turnover-cut"></strong></td>
							<td>量比：<strong>1.85</strong><br />换手：<strong _ntesquote_="code:1002002;fmt:huanshou;SCSTC27:274286.7188"></strong></td>
							<td class="add_btn_cont"><a href="" class="add_btn" data-code="1002002"><span>加入自选股</span></a></td>
						</tr>
						<tr class="stock_bref">
							<td><span  _ntesquote_="code:1002002;attr:time" class="refresh_time"></span></td>
							<td>流通市值：<span _ntesquote_="code:1002002;fmt:stockmcap;SCSTC27:274286.7188"></span></td>
							<td title='市盈率=最新股价/最近四个季度每股收益之和'>市盈率：<span _ntesquote_="code:1002002;fmt:pe;MFSUM:0.2826"></span></td>
							<td>52周最高：<span class="cRed">4.57</span></td>
							<td>52周最低：<span class="cGreen">2.73</span></td>
							<td></td>
						</tr>
					</table>
				</div>
			</td>
		</tr>
	</table>
</div>
<script>
	var MONEYSHOWLISTSAVE = 1;
</script>
    <script type="text/javascript">
        var STOCKCODE = '1002002';
        var STOCKSYMBOL = '002002';
        var STOCKNAME = '鸿达兴业';
    </script>
</div>
    <div id="menuCont" class="main_menu_cont">
    <ul class="main_menu clearfix">
                    <li class=""><a href="/1002002.html#01a01"><strong>鸿达兴业(002002)</strong></a></li>
                        <li class=""><a href="/trade/zjlx_002002.html#01b01">资金流向</a></li>
                        <li class="current active"><a href="/f10/zycwzb_002002.html#01c01">财务分析</a></li>
                        <li class=""><a href="/f10/gdfx_002002.html#01d01">股东股本</a></li>
                        <li class=""><a href="/f10/gsgg_002002.html#01e01">新闻公告</a></li>
                        <li class=""><a href="/f10/hydb_002002.html#01g01">行业对比</a></li>
                        <li class=""><a href="/f10/gszl_002002.html#01f01">公司资料</a></li>
                </ul>
    <div class="submenu_cont clearfix">
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=" last"><a href="/1002002.html#01a02">首页概览</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=""><a href="/trade/zjlx_002002.html#01b02">资金流向</a></li>
                                        <li class=""><a href="/trade/ddtj_002002.html#01b03">大单统计</a></li>
                                        <li class=""><a href="/trade/fjb_002002.html#01b04">分价表</a></li>
                                        <li class=""><a href="/trade/cjmx_002002.html#01b05">成交明细</a></li>
                                        <li class=""><a href="/trade/lhb_002002.html#01b06">龙虎榜</a></li>
                                        <li class=""><a href="/trade/lsjysj_002002.html#01b07">历史交易数据</a></li>
                                        <li class=" last"><a href="/trade/lszjlx_002002.html#01b08">历史资金流向</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class="current"><a href="/f10/zycwzb_002002.html#01c02">主要财务指标</a></li>
                                        <li class=""><a href="/f10/yjyg_002002.html#01c03">业绩预告</a></li>
                                        <li class=""><a href="/f10/cwbbzy_002002.html#01c04">财务报表摘要</a></li>
                                        <li class=""><a href="/f10/zcfzb_002002.html#01c05">资产负债表</a></li>
                                        <li class=""><a href="/f10/lrb_002002.html#01c06">利润表</a></li>
                                        <li class=""><a href="/f10/xjllb_002002.html#01c07">现金流量表</a></li>
                                        <li class=" last"><a href="/f10/dbfx_002002.html#01c08">杜邦分析</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=""><a href="/f10/gdfx_002002.html#01d02">股东分析</a></li>
                                        <li class=""><a href="/f10/jjcg_002002.html#01d03">基金持股</a></li>
                                        <li class=""><a href="/f10/nbcg_002002.html#01d04">内部持股</a></li>
                                        <li class=" last"><a href="/f10/fhpg_002002.html#01d05">分红配股</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=""><a href="/f10/gsgg_002002.html#01e02">公司公告</a></li>
                                        <li class=" last"><a href="/f10/gsxw_002002.html#01e03">公司新闻</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=""><a href="/f10/hydb_002002.html#01g02">行业对比</a></li>
                                        <li class=""><a href="/f10/hybk_002002.html#01g03">行业板块</a></li>
                                        <li class=""><a href="/f10/qybk_002002.html#01g05">区域板块</a></li>
                                        <li class=" last"><a href="/f10/zsbk_002002.html#01g06">指数板块</a></li>
                                </ul>
        </div>
                <div class="sub_menu tab_panel clearfix">
            <ul>
                                    <li class=" last"><a href="/f10/gszl_002002.html#01f02">公司资料</a></li>
                                </ul>
        </div>
            </div>
</div>
    <div class="blank9"></div>
    
<h1 class="title_01"> <span class="name">鸿达兴业(002002) 主要财务指标</span> </h1>
<div class="three_cols clearfix">
  <div class="inner_box">
    <div class="blank6"></div>
  <div class="scroll_table clearfix" id="scrollTable">
    <ul class="kchart_tab_title clearfix" style="margin:0;float:left;">
	          <li><a href="/f10/zycwzb_002002,report.html" class="current">按报告期<span>◆<em>◆</em></span></a></li>
      <li><a href="/f10/zycwzb_002002,year.html" class="">按年度<span>◆<em>◆</em></span></a></li>
	   <li><a href="/f10/zycwzb_002002,season.html" class="">按单季度<span>◆<em>◆</em></span></a></li>
    </ul>
	<a href="/service/zycwzb_002002.html?type=report" class="download_link" id="downloadData">下载数据</a>
	<div class="blank15"></div>
	<div class="clear"></div>
  <div class="col_1">
    <div class="chart_box chart_01"> <strong class="chart_title">净利润</strong>
      <div id="jlrChart"> </div>
    </div>
  </div>
  <div class="col_2  separate">
    <div class="chart_box chart_01"> <strong class="chart_title">主营收</strong>
      <div id="zysChart"> </div>
    </div>
  </div>
  <div class="col_3">
    <div class="chart_box chart_01"> <strong class="chart_title">每股收益</strong>
      <div id="mgsyChart"> </div>
    </div>
  </div>
  <div class="blank9"></div>
	<div class="col_l">
      <table class="table_bg001 border_box limit_sale">
	  	<thead>
			<tr class="dbrow title"><th class="align_l"><span class="scroll_btn_r active"></span><span class="scroll_btn_l"></span>报告日期</th></tr>
		</thead>
        <tbody>
        <tr>
          <td class="td_1">基本每股收益(元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">每股净资产(元)</td>
        </tr>
		<tr>
          <td class="td_1">每股经营活动产生的现金流量净额(元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">主营业务收入(万元)</td>
        </tr>
        <tr>
          <td class="td_1">主营业务利润(万元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">营业利润(万元)</td>
        </tr>
        <tr>
          <td class="td_1">投资收益(万元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">营业外收支净额(万元)</td>
        </tr>
        <tr>
          <td class="td_1">利润总额(万元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">净利润(万元)</td>
        </tr>
        <tr>
          <td class="td_1">净利润(扣除非经常性损益后)(万元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">经营活动产生的现金流量净额(万元)</td>
        </tr>
        <tr>
          <td class="td_1">现金及现金等价物净增加额(万元)</td>
        </tr>
        <tr class="dbrow">
          <td class="td_1">总资产(万元)</td>
        </tr>
        <tr>
          <td class="td_1">流动资产(万元)</td>
        </tr>
        <tr  class="dbrow">
          <td class="td_1">总负债(万元)</td>
        </tr>
        <tr>
          <td class="td_1">流动负债(万元)</td>
        </tr>
        <tr  class="dbrow">
          <td class="td_1">股东权益不含少数股东权益(万元)</td>
        </tr>
		<tr>
          <td class="td_1">净资产收益率加权(%)</td>
        </tr>
      </tbody></table>
    </div>
    <div class="col_r" style="">
      <table class="table_bg001 border_box limit_sale scr_table" >
		<tr class="dbrow"> <th >2020-09-30</th><th >2020-06-30</th><th >2020-03-31</th><th >2019-12-31</th><th >2019-09-30</th><th >2019-06-30</th><th >2019-03-31</th><th >2018-12-31</th><th >2018-09-30</th><th >2018-06-30</th><th >2018-03-31</th><th >2017-12-31</th><th >2017-09-30</th><th >2017-06-30</th><th >2017-03-31</th><th >2016-12-31</th><th >2016-09-30</th><th >2016-06-30</th><th >2016-03-31</th><th >2015-12-31</th><th >2015-09-30</th><th >2015-06-30</th><th >2015-03-31</th><th >2014-12-31</th><th >2014-09-30</th><th >2014-06-30</th><th >2014-03-31</th><th >2013-12-31</th><th >2013-09-30</th><th >2013-06-30</th><th >2013-03-31</th><th >2012-12-31</th><th >2012-09-30</th><th >2012-06-30</th><th >2012-03-31</th><th >2011-12-31</th><th >2011-09-30</th><th >2011-06-30</th><th >2011-03-31</th><th >2010-12-31</th><th >2010-09-30</th><th >2010-06-30</th><th >2010-03-31</th><th >2009-12-31</th><th >2009-09-30</th><th >2009-06-30</th><th >2009-03-31</th><th >2008-12-31</th><th >2008-09-30</th><th >2008-06-30</th><th >2008-03-31</th><th >2007-12-31</th><th >2007-09-30</th><th >2007-06-30</th><th >2007-03-31</th><th >2006-12-31</th><th >2006-09-30</th><th >2006-06-30</th><th >2006-03-31</th><th >2005-12-31</th><th >2005-09-30</th><th >2005-06-30</th><th >2005-03-31</th><th >2004-12-31</th><th >2004-09-30</th><th >2004-06-30</th><th >2003-12-31</th><th >2002-12-31</th><th >2001-12-31</th> </tr>
        <tr><td>0.23</td><td>0.13</td><td>0.07</td><td>0.24</td><td>0.19</td><td>0.11</td><td>0.07</td><td>0.24</td><td>0.26</td><td>0.16</td><td>0.10</td><td>0.41</td><td>0.35</td><td>0.21</td><td>0.13</td><td>0.34</td><td>0.21</td><td>0.11</td><td>0.11</td><td>0.57</td><td>0.36</td><td>0.24</td><td>0.09</td><td>0.41</td><td>0.30</td><td>0.15</td><td>0.10</td><td>0.58</td><td>0.38</td><td>0.22</td><td>0.00</td><td>0.01</td><td class='cRed'>-0.06</td><td class='cRed'>-0.06</td><td class='cRed'>-0.04</td><td>0.02</td><td class='cRed'>-0.18</td><td class='cRed'>-0.11</td><td class='cRed'>-0.06</td><td class='cRed'>-0.41</td><td class='cRed'>-0.16</td><td class='cRed'>-0.10</td><td class='cRed'>-0.06</td><td>0.06</td><td class='cRed'>-0.24</td><td class='cRed'>-0.12</td><td class='cRed'>-0.06</td><td class='cRed'>-0.77</td><td class='cRed'>-0.15</td><td class='cRed'>-0.15</td><td class='cRed'>-0.06</td><td class='cRed'>-0.21</td><td>0.01</td><td>0.01</td><td>0.01</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>
        <tr class="dbrow"><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>0.51</td><td>0.51</td><td>0.53</td><td>0.57</td><td>0.36</td><td>0.42</td><td>0.48</td><td>0.53</td><td>0.79</td><td>0.84</td><td>0.89</td><td>0.94</td><td>0.64</td><td>0.77</td><td>0.82</td><td>0.88</td><td>1.51</td><td>2.00</td><td>2.09</td><td>2.16</td><td>2.37</td><td>2.38</td><td>3.36</td><td>3.34</td><td>3.34</td><td>3.31</td><td>3.46</td><td>3.43</td><td>3.41</td><td>3.36</td><td>3.59</td><td>3.55</td><td>3.50</td><td>3.45</td><td>1.91</td><td>1.76</td><td>1.37</td></tr>
        <tr><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>0.05</td><td>0.03</td><td>0.02</td><td>0.10</td><td>0.00</td><td class='cRed'>-0.00</td><td>0.00</td><td>0.01</td><td>0.01</td><td>0.02</td><td class='cRed'>-0.01</td><td>0.07</td><td class='cRed'>-0.06</td><td class='cRed'>-0.07</td><td class='cRed'>-0.08</td><td>0.10</td><td>0.17</td><td>0.17</td><td class='cRed'>-0.04</td><td class='cRed'>-0.09</td><td>0.00</td><td>0.00</td><td class='cRed'>-0.14</td><td>0.15</td><td>0.00</td><td>--</td><td>0.00</td><td>0.32</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.21</td><td>0.00</td><td>0.00</td><td>0.50</td><td>0.00</td><td>0.00</td></tr>
        <tr class="dbrow"><td>392,828</td><td>261,811</td><td>144,209</td><td>529,965</td><td>405,644</td><td>284,612</td><td>140,526</td><td>604,470</td><td>432,247</td><td>293,643</td><td>141,345</td><td>654,063</td><td>482,137</td><td>307,325</td><td>149,621</td><td>615,774</td><td>359,470</td><td>223,679</td><td>128,149</td><td>380,998</td><td>262,627</td><td>165,330</td><td>72,329</td><td>332,001</td><td>218,267</td><td>124,782</td><td>56,754</td><td>241,657</td><td>172,474</td><td>115,924</td><td>5,556</td><td>20,825</td><td>14,380</td><td>8,994</td><td>4,937</td><td>18,090</td><td>13,596</td><td>9,415</td><td>4,408</td><td>20,304</td><td>15,553</td><td>10,577</td><td>4,562</td><td>17,661</td><td>14,136</td><td>9,065</td><td>4,112</td><td>32,708</td><td>29,418</td><td>18,813</td><td>8,410</td><td>34,112</td><td>29,815</td><td>19,988</td><td>7,436</td><td>29,609</td><td>22,442</td><td>14,577</td><td>6,784</td><td>29,471</td><td>22,417</td><td>15,333</td><td>7,273</td><td>28,150</td><td>20,761</td><td>13,768</td><td>23,037</td><td>22,102</td><td>19,883</td></tr>
        <tr><td>120,325</td><td>79,238</td><td>39,092</td><td>177,462</td><td class='cRed'>-2,392,466</td><td>81,810</td><td>40,722</td><td>187,430</td><td>152,975</td><td>97,936</td><td>48,269</td><td>227,098</td><td>176,599</td><td>108,359</td><td>54,070</td><td>184,495</td><td>110,341</td><td>63,255</td><td>24,190</td><td>113,881</td><td>69,741</td><td>47,775</td><td>17,794</td><td>77,323</td><td>51,556</td><td>30,692</td><td>14,061</td><td>59,858</td><td>36,769</td><td>24,133</td><td>582</td><td>1,313</td><td>932</td><td>492</td><td>232</td><td>50</td><td class='cRed'>-203</td><td class='cRed'>-449</td><td class='cRed'>-100</td><td class='cRed'>-150</td><td class='cRed'>-256</td><td class='cRed'>-296</td><td class='cRed'>-134</td><td class='cRed'>-109</td><td class='cRed'>-668</td><td class='cRed'>-647</td><td class='cRed'>-239</td><td>365</td><td>356</td><td>114</td><td class='cRed'>-32</td><td>1,901</td><td>2,506</td><td>1,737</td><td>--</td><td>4,333</td><td>3,269</td><td>2,265</td><td>1,009</td><td>5,505</td><td>4,160</td><td>2,794</td><td>1,260</td><td>5,286</td><td>3,974</td><td>2,704</td><td>5,497</td><td>6,336</td><td>5,281</td></tr>
        <tr class="dbrow"><td>68,046</td><td>39,259</td><td>21,776</td><td>74,422</td><td>57,006</td><td>33,102</td><td>22,513</td><td>75,481</td><td>80,098</td><td>50,660</td><td>30,727</td><td>123,091</td><td>106,805</td><td>62,608</td><td>37,881</td><td>101,359</td><td>63,341</td><td>33,525</td><td>12,872</td><td>65,266</td><td>38,957</td><td>23,290</td><td>9,967</td><td>41,202</td><td>29,130</td><td>14,484</td><td>7,125</td><td>33,843</td><td>21,095</td><td>11,632</td><td>10</td><td class='cRed'>-1,299</td><td class='cRed'>-946</td><td class='cRed'>-1,035</td><td class='cRed'>-672</td><td class='cRed'>-4,329</td><td class='cRed'>-2,959</td><td class='cRed'>-1,908</td><td class='cRed'>-948</td><td class='cRed'>-6,899</td><td class='cRed'>-2,634</td><td class='cRed'>-1,738</td><td class='cRed'>-940</td><td class='cRed'>-8,489</td><td class='cRed'>-4,207</td><td class='cRed'>-2,102</td><td class='cRed'>-1,109</td><td class='cRed'>-4,556</td><td class='cRed'>-2,734</td><td class='cRed'>-2,108</td><td class='cRed'>-844</td><td class='cRed'>-2,632</td><td>214</td><td>245</td><td>83</td><td>1,246</td><td>1,307</td><td>1,108</td><td>486</td><td>3,354</td><td>2,495</td><td>1,762</td><td>651</td><td>3,485</td><td>2,564</td><td>1,802</td><td>3,794</td><td>4,256</td><td>3,667</td></tr>
        <tr><td class='cRed'>-339</td><td>13</td><td class='cRed'>-109</td><td class='cRed'>-417</td><td class='cRed'>-393</td><td class='cRed'>-218</td><td class='cRed'>-210</td><td class='cRed'>-1,133</td><td class='cRed'>-1,212</td><td class='cRed'>-754</td><td class='cRed'>-394</td><td class='cRed'>-1,103</td><td class='cRed'>-617</td><td class='cRed'>-696</td><td class='cRed'>-374</td><td class='cRed'>-460</td><td>1,027</td><td class='cRed'>-470</td><td class='cRed'>-584</td><td>1,757</td><td class='cRed'>-58</td><td class='cRed'>-58</td><td>--</td><td>68</td><td>256</td><td>256</td><td>--</td><td>452</td><td>457</td><td class='cRed'>-35</td><td>--</td><td>0</td><td class='cRed'>-0</td><td class='cRed'>-0</td><td class='cRed'>-0</td><td>0</td><td>--</td><td>--</td><td>--</td><td>51</td><td>57</td><td>57</td><td>57</td><td>0</td><td>--</td><td>0</td><td>--</td><td>1</td><td>1</td><td>1</td><td>0</td><td>81</td><td>31</td><td>--</td><td>0</td><td>20</td><td>9</td><td>3</td><td>1</td><td>12</td><td>9</td><td>6</td><td>0</td><td class='cRed'>-48</td><td class='cRed'>-55</td><td class='cRed'>-62</td><td>47</td><td class='cRed'>-0</td><td>75</td></tr>
        <tr class="dbrow"><td>643</td><td>389</td><td>75</td><td class='cRed'>-49</td><td>1,054</td><td>163</td><td>136</td><td class='cRed'>-126</td><td>399</td><td class='cRed'>-10</td><td>11</td><td class='cRed'>-487</td><td>341</td><td>241</td><td>245</td><td>2,232</td><td>2,164</td><td>919</td><td>922</td><td>1,259</td><td>1,512</td><td>1,544</td><td class='cRed'>-23</td><td>1,691</td><td>1,761</td><td>285</td><td>251</td><td>2,177</td><td>1,307</td><td>1,302</td><td>12</td><td>1,522</td><td class='cRed'>-17</td><td class='cRed'>-5</td><td class='cRed'>-6</td><td>4,620</td><td class='cRed'>-3</td><td class='cRed'>-2</td><td class='cRed'>-6</td><td>72</td><td>32</td><td>35</td><td>11</td><td>8,865</td><td class='cRed'>-10</td><td>8</td><td>10</td><td class='cRed'>-8,856</td><td>--</td><td class='cRed'>-50</td><td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>169</td><td>0</td><td>--</td><td>0</td><td class='cRed'>-63</td><td>0</td><td>0</td><td>0</td><td class='cRed'>-76</td><td>0</td><td>0</td><td class='cRed'>-52</td><td>0</td><td>0</td></tr>
        <tr><td>68,689</td><td>39,648</td><td>21,851</td><td>74,373</td><td>58,060</td><td>33,266</td><td>22,649</td><td>75,355</td><td>80,498</td><td>50,650</td><td>30,738</td><td>122,604</td><td>107,146</td><td>62,849</td><td>38,126</td><td>103,591</td><td>65,504</td><td>34,444</td><td>13,794</td><td>66,525</td><td>40,469</td><td>24,833</td><td>9,944</td><td>42,894</td><td>30,891</td><td>14,769</td><td>7,376</td><td>36,021</td><td>22,402</td><td>12,934</td><td>21</td><td>223</td><td class='cRed'>-963</td><td class='cRed'>-1,040</td><td class='cRed'>-678</td><td>291</td><td class='cRed'>-2,962</td><td class='cRed'>-1,909</td><td class='cRed'>-954</td><td class='cRed'>-6,826</td><td class='cRed'>-2,602</td><td class='cRed'>-1,703</td><td class='cRed'>-929</td><td>376</td><td class='cRed'>-4,217</td><td class='cRed'>-2,094</td><td class='cRed'>-1,099</td><td class='cRed'>-13,412</td><td class='cRed'>-2,807</td><td class='cRed'>-2,158</td><td class='cRed'>-875</td><td class='cRed'>-2,823</td><td>166</td><td>219</td><td>62</td><td>1,435</td><td>1,388</td><td>1,103</td><td>472</td><td>3,303</td><td>2,501</td><td>1,742</td><td>645</td><td>3,362</td><td>2,485</td><td>1,739</td><td>3,789</td><td>4,204</td><td>3,725</td></tr>
        <tr class="dbrow"><td>58,377</td><td>33,196</td><td>19,090</td><td>62,995</td><td>48,696</td><td>27,518</td><td>18,999</td><td>61,091</td><td>66,473</td><td>41,975</td><td>25,202</td><td>100,488</td><td>85,647</td><td>50,496</td><td>30,420</td><td>81,780</td><td>52,167</td><td>27,604</td><td>10,841</td><td>51,909</td><td>31,668</td><td>20,347</td><td>8,059</td><td>34,705</td><td>25,618</td><td>12,377</td><td>6,164</td><td>29,563</td><td>19,132</td><td>10,800</td><td>21</td><td>223</td><td class='cRed'>-963</td><td class='cRed'>-1,040</td><td class='cRed'>-678</td><td>325</td><td class='cRed'>-2,959</td><td class='cRed'>-1,907</td><td class='cRed'>-953</td><td class='cRed'>-6,814</td><td class='cRed'>-2,600</td><td class='cRed'>-1,702</td><td class='cRed'>-929</td><td>961</td><td class='cRed'>-4,018</td><td class='cRed'>-1,971</td><td class='cRed'>-1,026</td><td class='cRed'>-12,923</td><td class='cRed'>-2,546</td><td class='cRed'>-1,956</td><td class='cRed'>-787</td><td class='cRed'>-2,665</td><td>127</td><td>170</td><td>51</td><td>1,018</td><td>989</td><td>759</td><td>323</td><td>2,008</td><td>1,494</td><td>1,030</td><td>394</td><td>2,002</td><td>1,476</td><td>1,020</td><td>2,258</td><td>2,486</td><td>2,298</td></tr>
        <tr><td>56,930</td><td>32,393</td><td>18,880</td><td>60,115</td><td>46,222</td><td>26,548</td><td>18,548</td><td>59,253</td><td>65,852</td><td>41,522</td><td>25,102</td><td>99,438</td><td>85,375</td><td>50,302</td><td>30,222</td><td>79,926</td><td>50,197</td><td>26,815</td><td>10,297</td><td>50,618</td><td>30,187</td><td>18,834</td><td>8,074</td><td>33,263</td><td>24,126</td><td>12,136</td><td>5,919</td><td>24,647</td><td>14,235</td><td>5,901</td><td>10</td><td class='cRed'>-1,299</td><td>--</td><td class='cRed'>-1,035</td><td>--</td><td class='cRed'>-4,286</td><td>--</td><td class='cRed'>-1,909</td><td>--</td><td class='cRed'>-6,959</td><td>--</td><td class='cRed'>-1,791</td><td>--</td><td class='cRed'>-7,889</td><td>--</td><td class='cRed'>-1,983</td><td>0</td><td class='cRed'>-4,065</td><td>0</td><td class='cRed'>-1,892</td><td>0</td><td class='cRed'>-2,483</td><td>0</td><td>178</td><td>--</td><td>899</td><td>0</td><td>756</td><td>0</td><td>1,993</td><td>0</td><td>1,046</td><td>0</td><td>2,094</td><td>0</td><td>1,057</td><td>0</td><td>0</td><td>0</td></tr>
        <tr class="dbrow"><td class='cRed'>-33,039</td><td class='cRed'>-70,743</td><td class='cRed'>-77,628</td><td>45,551</td><td>106,970</td><td>56,538</td><td>66,300</td><td>142,996</td><td>67,373</td><td>46,691</td><td>3,574</td><td>87,052</td><td>27,734</td><td>3,671</td><td>3,411</td><td>63,308</td><td>1,924</td><td class='cRed'>-4,328</td><td>27,772</td><td>33,167</td><td>21,567</td><td>26,830</td><td class='cRed'>-1,741</td><td class='cRed'>-9,882</td><td class='cRed'>-3,911</td><td class='cRed'>-3,979</td><td class='cRed'>-6,967</td><td class='cRed'>-6,188</td><td class='cRed'>-1,531</td><td class='cRed'>-3,142</td><td>140</td><td class='cRed'>-1,161</td><td>785</td><td>450</td><td>380</td><td>1,651</td><td>24</td><td class='cRed'>-44</td><td>33</td><td>107</td><td>196</td><td>374</td><td class='cRed'>-157</td><td>1,209</td><td class='cRed'>-1,049</td><td class='cRed'>-1,101</td><td class='cRed'>-1,319</td><td>1,698</td><td>2,762</td><td>2,153</td><td class='cRed'>-507</td><td class='cRed'>-1,184</td><td>50</td><td>58</td><td class='cRed'>-1,238</td><td>1,387</td><td class='cRed'>-2,671</td><td class='cRed'>-3,867</td><td class='cRed'>-4,417</td><td>2,895</td><td>4,142</td><td>1,167</td><td class='cRed'>-772</td><td>1,948</td><td>650</td><td class='cRed'>-97</td><td>3,086</td><td>0</td><td>0</td></tr>
        <tr><td class='cRed'>-192,483</td><td class='cRed'>-180,897</td><td class='cRed'>-150,476</td><td>169,481</td><td class='cRed'>-40,434</td><td class='cRed'>-36,578</td><td class='cRed'>-32,372</td><td class='cRed'>-76,703</td><td class='cRed'>-58,767</td><td class='cRed'>-48,762</td><td class='cRed'>-20,171</td><td>52,638</td><td>53,311</td><td class='cRed'>-34,757</td><td class='cRed'>-7,675</td><td class='cRed'>-21,922</td><td class='cRed'>-27,646</td><td class='cRed'>-40,167</td><td class='cRed'>-23,115</td><td>8,714</td><td>24,229</td><td>44,338</td><td class='cRed'>-11,929</td><td>40,777</td><td>44,122</td><td>8,117</td><td class='cRed'>-2,073</td><td>23,343</td><td>9,925</td><td class='cRed'>-2,426</td><td>910</td><td>1,111</td><td>1,519</td><td>2,851</td><td>3,276</td><td class='cRed'>-14</td><td class='cRed'>-301</td><td class='cRed'>-295</td><td class='cRed'>-63</td><td class='cRed'>-178</td><td class='cRed'>-130</td><td>393</td><td>155</td><td>628</td><td class='cRed'>-1,735</td><td class='cRed'>-1,853</td><td class='cRed'>-1,632</td><td class='cRed'>-7,557</td><td class='cRed'>-4,412</td><td class='cRed'>-4,315</td><td class='cRed'>-1,742</td><td class='cRed'>-3,435</td><td class='cRed'>-373</td><td>1,062</td><td>2,112</td><td class='cRed'>-11,079</td><td class='cRed'>-11,142</td><td class='cRed'>-13,305</td><td class='cRed'>-3,436</td><td class='cRed'>-5,444</td><td>691</td><td class='cRed'>-326</td><td>1,228</td><td>24,406</td><td>25,039</td><td>23,877</td><td class='cRed'>-973</td><td>0</td><td>0</td></tr>
        <tr class="dbrow"><td>1,653,798</td><td>1,701,353</td><td>1,722,712</td><td>1,680,764</td><td>1,360,722</td><td>1,381,688</td><td>1,360,303</td><td>1,414,195</td><td>1,373,663</td><td>1,378,751</td><td>1,443,141</td><td>1,433,765</td><td>1,434,748</td><td>1,302,388</td><td>1,293,518</td><td>1,273,798</td><td>1,247,049</td><td>1,218,259</td><td>1,189,016</td><td>1,163,146</td><td>1,170,559</td><td>1,107,130</td><td>1,001,484</td><td>974,902</td><td>918,103</td><td>829,483</td><td>739,769</td><td>704,852</td><td>601,679</td><td>512,341</td><td>31,728</td><td>30,128</td><td>30,741</td><td>30,083</td><td>30,799</td><td>25,874</td><td>25,982</td><td>26,442</td><td>27,535</td><td>28,166</td><td>31,782</td><td>32,588</td><td>32,863</td><td>36,268</td><td>41,465</td><td>42,909</td><td>44,711</td><td>47,448</td><td>53,292</td><td>53,484</td><td>58,297</td><td>58,913</td><td>59,250</td><td>59,954</td><td>60,347</td><td>55,020</td><td>55,085</td><td>51,598</td><td>53,508</td><td>54,827</td><td>55,706</td><td>51,593</td><td>53,540</td><td>47,679</td><td>48,581</td><td>47,427</td><td>25,313</td><td>22,405</td><td>18,128</td></tr>
        <tr><td>628,311</td><td>703,291</td><td>802,736</td><td>755,755</td><td>439,129</td><td>457,975</td><td>446,695</td><td>492,904</td><td>475,431</td><td>474,481</td><td>536,553</td><td>523,329</td><td>563,457</td><td>425,136</td><td>412,267</td><td>393,000</td><td>400,675</td><td>363,021</td><td>351,624</td><td>326,417</td><td>333,898</td><td>316,159</td><td>255,922</td><td>246,556</td><td>305,157</td><td>277,708</td><td>216,309</td><td>202,345</td><td>200,258</td><td>147,533</td><td>11,362</td><td>10,001</td><td>10,610</td><td>10,038</td><td>11,071</td><td>5,676</td><td>5,345</td><td>5,294</td><td>5,927</td><td>6,107</td><td>6,374</td><td>6,599</td><td>6,265</td><td>5,839</td><td>6,476</td><td>6,604</td><td>7,493</td><td>9,342</td><td>16,929</td><td>15,597</td><td>22,076</td><td>23,192</td><td>24,897</td><td>26,381</td><td>27,528</td><td>22,811</td><td>25,755</td><td>24,587</td><td>32,934</td><td>34,769</td><td>38,896</td><td>37,111</td><td>41,202</td><td>36,832</td><td>38,310</td><td>36,926</td><td>14,373</td><td>13,211</td><td>10,912</td></tr>
        <tr class="dbrow"><td>878,333</td><td>935,422</td><td>972,590</td><td>948,301</td><td>699,962</td><td>742,255</td><td>726,931</td><td>799,779</td><td>751,945</td><td>781,045</td><td>833,667</td><td>849,360</td><td>869,918</td><td>889,378</td><td>876,406</td><td>887,045</td><td>872,388</td><td>869,748</td><td>852,691</td><td>743,794</td><td>769,551</td><td>818,177</td><td>710,114</td><td>691,589</td><td>644,353</td><td>568,970</td><td>485,769</td><td>457,016</td><td>446,575</td><td>365,569</td><td>21,939</td><td>20,360</td><td>22,159</td><td>21,578</td><td>21,932</td><td>16,214</td><td>19,895</td><td>19,302</td><td>19,441</td><td>19,117</td><td>18,509</td><td>18,416</td><td>17,917</td><td>20,100</td><td>29,855</td><td>29,177</td><td>29,972</td><td>31,617</td><td>26,739</td><td>26,284</td><td>29,793</td><td>29,558</td><td>26,981</td><td>27,608</td><td>27,543</td><td>22,421</td><td>22,489</td><td>19,211</td><td>19,729</td><td>21,382</td><td>21,365</td><td>19,576</td><td>19,264</td><td>13,850</td><td>15,296</td><td>14,667</td><td>12,282</td><td>10,195</td><td>8,480</td></tr>
        <tr><td>661,156</td><td>714,998</td><td>733,651</td><td>698,229</td><td>618,529</td><td>644,004</td><td>578,836</td><td>671,759</td><td>610,724</td><td>638,584</td><td>666,247</td><td>660,598</td><td>639,295</td><td>653,094</td><td>643,034</td><td>683,312</td><td>649,015</td><td>670,105</td><td>630,005</td><td>534,290</td><td>544,225</td><td>591,265</td><td>467,824</td><td>470,416</td><td>413,999</td><td>375,981</td><td>305,660</td><td>294,338</td><td>247,812</td><td>217,174</td><td>21,939</td><td>20,360</td><td>22,159</td><td>21,578</td><td>21,932</td><td>16,214</td><td>19,891</td><td>19,298</td><td>19,437</td><td>19,113</td><td>18,505</td><td>18,412</td><td>17,913</td><td>20,096</td><td>20,981</td><td>20,303</td><td>21,099</td><td>22,744</td><td>26,135</td><td>25,080</td><td>28,587</td><td>28,351</td><td>25,777</td><td>26,104</td><td>26,039</td><td>19,899</td><td>20,985</td><td>19,207</td><td>19,725</td><td>20,974</td><td>20,947</td><td>19,093</td><td>18,782</td><td>13,781</td><td>15,227</td><td>14,598</td><td>12,213</td><td>10,150</td><td>8,480</td></tr>
        <tr class="dbrow"><td>770,281</td><td>760,456</td><td>744,718</td><td>727,026</td><td>655,480</td><td>634,176</td><td>627,994</td><td>608,995</td><td>616,585</td><td>592,633</td><td>604,291</td><td>579,088</td><td>560,320</td><td>408,808</td><td>412,684</td><td>382,264</td><td>369,855</td><td>344,112</td><td>332,320</td><td>415,417</td><td>398,590</td><td>286,851</td><td>291,084</td><td>283,024</td><td>273,454</td><td>260,213</td><td>254,000</td><td>247,836</td><td>155,104</td><td>146,772</td><td>9,789</td><td>9,768</td><td>8,582</td><td>8,505</td><td>8,867</td><td>9,545</td><td>5,940</td><td>6,991</td><td>7,945</td><td>8,899</td><td>13,112</td><td>14,011</td><td>14,784</td><td>15,713</td><td>10,735</td><td>12,782</td><td>13,727</td><td>14,753</td><td>25,129</td><td>25,720</td><td>26,889</td><td>27,676</td><td>30,468</td><td>30,511</td><td>30,850</td><td>30,609</td><td>30,580</td><td>30,350</td><td>31,748</td><td>31,425</td><td>31,298</td><td>30,834</td><td>32,949</td><td>32,554</td><td>32,069</td><td>31,613</td><td>11,802</td><td>10,835</td><td>8,425</td></tr>
		<tr><td>7.75</td><td>4.46</td><td>2.59</td><td>9.84</td><td>7.54</td><td>4.41</td><td>3.07</td><td>10.31</td><td>11.09</td><td>7.40</td><td>4.26</td><td>21.93</td><td>20.03</td><td>12.51</td><td>7.65</td><td>23.62</td><td>14.82</td><td>7.87</td><td>2.85</td><td>15.28</td><td>9.89</td><td>7.00</td><td>2.81</td><td>13.08</td><td>9.86</td><td>4.87</td><td>2.46</td><td>18.50</td><td>12.93</td><td>7.55</td><td>0.22</td><td>2.31</td><td class='cRed'>-10.63</td><td class='cRed'>-11.52</td><td class='cRed'>-7.37</td><td>3.57</td><td class='cRed'>-39.88</td><td class='cRed'>-24.01</td><td class='cRed'>-11.32</td><td class='cRed'>-55.37</td><td class='cRed'>-18.04</td><td class='cRed'>-11.45</td><td class='cRed'>-6.09</td><td>6.31</td><td>--</td><td class='cRed'>-14.31</td><td>0.00</td><td class='cRed'>-60.92</td><td>0.00</td><td class='cRed'>-7.33</td><td>0.00</td><td class='cRed'>-9.12</td><td>0.00</td><td>0.55</td><td>--</td><td>3.30</td><td>0.00</td><td>2.41</td><td>0.00</td><td>5.98</td><td>0.00</td><td>3.43</td><td>0.00</td><td>9.23</td><td>0.00</td><td>9.04</td><td>20.65</td><td>25.72</td><td>31.40</td></tr>
      </table>
    </div>
</div>
</div>
<div class="blank15"></div>
<h2 class="title_01"><a href="/service/zycwzb_002002.html?type=report&part=ylnl" class="download_link" id="downloadData" style="float: right;margin: 6px;">下载数据</a> <span class="name">盈利能力</span> </h2>
<div class="inner_box two_cols clearfix">
  <div class="col_1">
    <div class="chart_box chart_01"> <strong class="chart_title">营业利润率</strong>
      <div id="ylnlCharts1" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>营业利润率</p>
  </div>
  <div class="col_2">
    <div class="chart_box chart_01"> <strong class="chart_title">净资产收益率</strong>
      <div id="ylnlCharts2" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>净资产收益率</p>
  </div>
  <div class="blank15"></div>
  <div class="inner_box">
    <table class="table_bg001 border_box fund_analys">
      <thead>
        <tr class="dbrow">
          <th></th>
          <th >2020-09-30</th><th >2020-06-30</th><th >2020-03-31</th><th >2019-12-31</th><th >2019-09-30</th><th >2019-06-30</th></tr>
      </thead>
      <tr>
        <td class="td_1">总资产利润率(%)</td>
        <td>3.51</td><td>1.95</td><td>1.11</td><td>3.75</td><td>3.57</td><td>1.98</td></tr>
      <tr class="dbrow">
        <td class="td_1">主营业务利润率(%)</td>
        <td>30.63</td><td>30.27</td><td>27.11</td><td>33.49</td><td class='cRed'>-589.79</td><td>28.74</td></tr>
      <tr>
        <td class="td_1">总资产净利润率(%)</td>
        <td>3.49</td><td>1.97</td><td>1.12</td><td>4.07</td><td>3.50</td><td>1.96</td></tr>
      <tr class="dbrow">
        <td class="td_1">成本费用利润率(%)</td>
        <td>21.84</td><td>18.52</td><td>17.99</td><td>17.16</td><td>2.03</td><td>13.55</td></tr>
      <tr>
        <td class="td_1">营业利润率(%)</td>
        <td>17.32</td><td>15.00</td><td>15.10</td><td>14.04</td><td>14.05</td><td>11.63</td></tr>
      <tr class="dbrow">
        <td class="td_1">主营业务成本率(%)</td>
        <td>68.51</td><td>68.83</td><td>71.93</td><td>65.25</td><td>688.61</td><td>70.02</td></tr>
      <tr>
        <td class="td_1">销售净利率(%)</td>
        <td>14.80</td><td>12.69</td><td>13.22</td><td>11.89</td><td>11.97</td><td>9.61</td></tr>
      <tr class="dbrow">
        <td class="td_1">净资产收益率(%)</td>
        <td>7.58</td><td>4.37</td><td>2.56</td><td>8.66</td><td>7.43</td><td>4.34</td></tr>
      <tr>
        <td class="td_1">股本报酬率(%)</td>
        <td>22.45</td><td>107.98</td><td>7.36</td><td>112.56</td><td>18.76</td><td>92.29</td></tr>
      <tr class="dbrow">
        <td class="td_1">净资产报酬率(%)</td>
        <td>7.50</td><td>36.50</td><td>2.54</td><td>39.78</td><td>7.35</td><td>37.36</td></tr>
      <tr>
        <td class="td_1">资产报酬率(%)</td>
        <td>3.51</td><td>16.43</td><td>1.11</td><td>17.34</td><td>3.57</td><td>17.29</td></tr>
      <tr class="dbrow">
        <td class="td_1">销售毛利率(%)</td>
        <td>--</td><td>--</td><td>--</td><td>--</td><td>--</td><td>29.98</td></tr>
      <tr>
        <td class="td_1">三项费用比重(%)</td>
        <td>10.68</td><td>12.03</td><td>11.33</td><td>15.26</td><td>14.16</td><td>15.02</td></tr>
      <tr class="dbrow">
        <td class="td_1">非主营比重(%)</td>
        <td>0.44</td><td>1.01</td><td class='cRed'>-0.16</td><td class='cRed'>-0.63</td><td>1.14</td><td class='cRed'>-0.17</td></tr>
      <tr>
        <td class="td_1">主营利润比重(%)</td>
        <td>175.17</td><td>199.85</td><td>178.90</td><td>238.61</td><td class='cRed'>-4,120.69</td><td>245.93</td></tr>
     <!-- <tr class="dbrow">
        <td class="td_1">股息发放率</td>
        </tr>-->
    </table>
  </div>
</div>
<div class="blank15"></div>
<h2 class="title_01">  <a href="/service/zycwzb_002002.html?type=report&part=chnl" class="download_link" id="downloadData" style="float: right;margin: 6px;">下载数据</a> <span class="name">偿还能力</span></h2>
<div class="inner_box two_cols clearfix">
  <div class="col_1">
    <div class="chart_box chart_01"> <strong class="chart_title">流动比率</strong>
      <div id="chnlCharts1" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>流动比率</p>
  </div>
  <div class="col_2">
    <div class="chart_box chart_01"> <strong class="chart_title">资产负债率</strong>
      <div id="chnlCharts2" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>资产负债率</p>
  </div>
  <div class="blank15"></div>
  <div class="inner_box">
    <table class="table_bg001 border_box fund_analys">
      <thead>
        <tr class="dbrow">
          <th></th>
          <th >2020-09-30</th><th >2020-06-30</th><th >2020-03-31</th><th >2019-12-31</th><th >2019-09-30</th><th >2019-06-30</th></tr>
      </thead>
      <tr>
        <td class="td_1">流动比率(%)</td>
        <td>0.95</td><td>0.98</td><td>1.09</td><td>1.08</td><td>0.71</td><td>0.71</td></tr>
      <tr class="dbrow">
        <td class="td_1">速动比率(%)</td>
        <td>0.83</td><td>0.89</td><td>1.00</td><td>1.00</td><td>0.62</td><td>0.63</td></tr>
      <tr>
        <td class="td_1">现金比率(%)</td>
        <td>14.36</td><td>21.16</td><td>35.02</td><td>45.23</td><td>14.47</td><td>17.11</td></tr>
      <tr class="dbrow">
        <td class="td_1">利息支付倍数(%)</td>
        <td>355.86</td><td>289.21</td><td>414.06</td><td>326.17</td><td>330.06</td><td>282.63</td></tr>
      <tr>
        <td class="td_1">资产负债率(%)</td>
        <td>53.11</td><td>54.98</td><td>56.46</td><td>56.42</td><td>51.44</td><td>53.72</td></tr>
      <tr class="dbrow">
        <td class="td_1">长期债务与营运资金比率(%)</td>
        <td class='cRed'>-0.06</td><td class='cRed'>-0.24</td><td>0.15</td><td>0.29</td><td class='cRed'>-0.30</td><td class='cRed'>-0.33</td></tr>
      <tr>
        <td class="td_1">股东权益比率(%)</td>
        <td>46.89</td><td>45.02</td><td>43.54</td><td>43.58</td><td>48.56</td><td>46.28</td></tr>
      <tr class="dbrow">
        <td class="td_1">长期负债比率(%)</td>
        <td>0.12</td><td>0.17</td><td>0.61</td><td>1.00</td><td>4.01</td><td>4.38</td></tr>
      <tr>
        <td class="td_1">股东权益与固定资产比率(%)</td>
        <td>--</td><td>100.38</td><td>--</td><td>99.34</td><td>--</td><td>85.34</td></tr>
      <tr class="dbrow">
        <td class="td_1">负债与所有者权益比率(%)</td>
        <td>113.27</td><td>122.13</td><td>129.66</td><td>129.47</td><td>105.93</td><td>116.08</td></tr>
      <tr>
        <td class="td_1">长期资产与长期资金比率(%)</td>
        <td>131.90</td><td>129.83</td><td>120.95</td><td>123.45</td><td>128.85</td><td>131.97</td></tr>
      <tr class="dbrow">
        <td class="td_1">资本化比率(%)</td>
        <td>0.26</td><td>0.37</td><td>1.38</td><td>2.25</td><td>7.62</td><td>8.64</td></tr>
      <tr>
        <td class="td_1">固定资产净值率(%)</td>
        <td>--</td><td>75.60</td><td>--</td><td>76.35</td><td>--</td><td>77.98</td></tr>
      <tr class="dbrow">
        <td class="td_1">资本固定化比率(%)</td>
        <td>132.24</td><td>130.31</td><td>122.64</td><td>126.29</td><td>139.47</td><td>144.46</td></tr>
      <tr>
        <td class="td_1">产权比率(%)</td>
        <td>85.52</td><td>93.72</td><td>99.20</td><td>97.63</td><td>101.86</td><td>110.18</td></tr>
      <tr class="dbrow">
        <td class="td_1">清算价值比率(%)</td>
        <td>243.35</td><td>231.29</td><td>226.03</td><td>229.29</td><td>195.97</td><td>190.15</td></tr>
      <tr>
        <td class="td_1">固定资产比重(%)</td>
        <td>--</td><td>44.85</td><td>--</td><td>43.87</td><td>--</td><td>54.23</td></tr>
    </table>
  </div>
</div>
<div class="blank15"></div>
<h2 class="title_01">  <a href="/service/zycwzb_002002.html?type=report&part=cznl" class="download_link" id="downloadData" style="float: right;margin: 6px;">下载数据</a> <span class="name">成长能力</span></h2>

<div class="inner_box two_cols clearfix">
  <div class="col_1">
    <div class="chart_box chart_01"> <strong class="chart_title">净利润增长率</strong>
      <div id="cznlCharts1" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>净利润增长率 &nbsp;&nbsp;&nbsp;</p>
  </div>
  <div class="col_2">
    <div class="chart_box chart_01"> <strong class="chart_title">净资产增长率</strong>
      <div id="cznlCharts2" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>净资产增长率 &nbsp;&nbsp;&nbsp;</p>
  </div>
  <div class="blank15"></div>
  <div class="inner_box">
    <table class="table_bg001 border_box fund_analys">
      <thead>
        <tr class="dbrow">
          <th></th>
          <th >2020-09-30</th><th >2020-06-30</th><th >2020-03-31</th><th >2019-12-31</th><th >2019-09-30</th><th >2019-06-30</th></tr>
      </thead>
      <tr>
        <td class="td_1">主营业务收入增长率(%)</td>
        <td class='cRed'>-3.16</td><td class='cRed'>-8.01</td><td>2.62</td><td class='cRed'>-12.33</td><td class='cRed'>-6.15</td><td class='cRed'>-3.08</td></tr>
      <tr class="dbrow">
        <td class="td_1">净利润增长率(%)</td>
        <td>19.71</td><td>21.50</td><td>0.53</td><td>2.97</td><td class='cRed'>-26.75</td><td class='cRed'>-34.45</td></tr>
      <tr>
        <td class="td_1">净资产增长率(%)</td>
        <td>17.36</td><td>19.78</td><td>18.43</td><td>19.21</td><td>6.28</td><td>6.98</td></tr>
      <tr class="dbrow">
        <td class="td_1">总资产增长率(%)</td>
        <td>21.54</td><td>23.14</td><td>26.64</td><td>18.85</td><td class='cRed'>-0.94</td><td>0.21</td></tr>
    </table>
  </div>
</div>
<div class="blank15"></div>
<h2 class="title_01">  <a href="/service/zycwzb_002002.html?type=report&part=yynl" class="download_link" id="downloadData" style="float: right;margin: 6px;">下载数据</a> <span class="name">营运能力</span></h2>

<div class="inner_box two_cols clearfix">
  <div class="col_1">
    <div class="chart_box chart_01"> <strong class="chart_title">存货周转率(次)</strong>
      <div id="yynlCharts1" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>存货周转率(次)</p>
  </div>
  <div class="col_2">
    <div class="chart_box chart_01"> <strong class="chart_title">总资产周转率(次)</strong>
      <div id="yynlCharts2" class="dbcolor_chart"> </div>
    </div>
    <p class="guide_line_cont"><span class="guide_line guide_line_a"></span>总资产周转率(次)</p>
  </div>
  <div class="blank15"></div>
  <div class="inner_box">
    <table class="table_bg001 border_box fund_analys">
      <thead>
        <tr class="dbrow">
          <th></th>
          <th >2020-09-30</th><th >2020-06-30</th><th >2020-03-31</th><th >2019-12-31</th><th >2019-09-30</th><th >2019-06-30</th></tr>
      </thead>
      <tr>
        <td class="td_1">应收账款周转率(次)</td>
        <td>1.86</td><td>1.28</td><td>0.73</td><td>2.86</td><td>2.22</td><td>1.52</td></tr>
      <tr class="dbrow">
        <td class="td_1">应收账款周转天数(天)</td>
        <td>144.89</td><td>140.55</td><td>123.95</td><td>125.72</td><td>121.68</td><td>118.49</td></tr>
      <tr>
        <td class="td_1">存货周转率(次)</td>
        <td>3.92</td><td>2.87</td><td>1.63</td><td>5.76</td><td>48.30</td><td>3.45</td></tr>
      <tr class="dbrow">
        <td class="td_1">固定资产周转率(次)</td>
        <td>--</td><td>0.35</td><td>--</td><td>0.71</td><td>--</td><td>0.38</td></tr>
      <tr>
        <td class="td_1">总资产周转率(次)</td>
        <td>0.24</td><td>0.15</td><td>0.08</td><td>0.34</td><td>0.29</td><td>0.20</td></tr>
      <tr class="dbrow">
        <td class="td_1">存货周转天数(天)</td>
        <td>68.91</td><td>62.70</td><td>55.19</td><td>62.53</td><td>5.59</td><td>52.13</td></tr>
      <tr>
        <td class="td_1">总资产周转天数(天)</td>
        <td>1,146.01</td><td>1,162.79</td><td>1,062.57</td><td>1,051.09</td><td>923.39</td><td>884.09</td></tr>
      <tr class="dbrow">
        <td class="td_1">流动资产周转率(次)</td>
        <td>0.57</td><td>0.36</td><td>0.19</td><td>0.85</td><td>0.87</td><td>0.60</td></tr>
      <tr>
        <td class="td_1">流动资产周转天数(天)</td>
        <td>475.69</td><td>501.53</td><td>486.22</td><td>424.08</td><td>310.20</td><td>300.70</td></tr>
      <tr class="dbrow">
        <td class="td_1">经营现金净流量对销售收入比率(%)</td>
        <td class='cRed'>-0.08</td><td class='cRed'>-0.27</td><td class='cRed'>-0.54</td><td>0.09</td><td>0.26</td><td>0.20</td></tr>
      <tr>
        <td class="td_1">资产的经营现金流量回报率(%)</td>
        <td class='cRed'>-0.02</td><td class='cRed'>-0.04</td><td class='cRed'>-0.05</td><td>0.03</td><td>0.08</td><td>0.04</td></tr>
      <tr class="dbrow">
        <td class="td_1">经营现金净流量与净利润的比率(%)</td>
        <td class='cRed'>-0.57</td><td class='cRed'>-2.13</td><td class='cRed'>-4.07</td><td>0.72</td><td>2.20</td><td>2.07</td></tr>
      <tr>
        <td class="td_1">经营现金净流量对负债比率(%)</td>
        <td class='cRed'>-0.04</td><td class='cRed'>-0.08</td><td class='cRed'>-0.08</td><td>0.05</td><td>0.15</td><td>0.08</td></tr>
      <tr class="dbrow">
        <td class="td_1">现金流量比率(%)</td>
        <td class='cRed'>-5.00</td><td class='cRed'>-9.89</td><td class='cRed'>-10.58</td><td>6.52</td><td>17.29</td><td>8.78</td></tr>
    </table>
  </div>
</div>
<em id="pageIdentityCode" data-code="e1"></em> 
<script>
var jlrChart = [{"key":"20Q3","value":583766928.53},{"key":"20Q2","value":331964253.3},{"key":"20Q1","value":190903628.85},{"key":"19Q4","value":629948190.8},{"key":"19Q3","value":486955967.56},{"key":"19Q2","value":275178223.78}];
var zysChart = [{"key":"20Q3","value":3928276359.66},{"key":"20Q2","value":2618113235.74},{"key":"20Q1","value":1442090846.51},{"key":"19Q4","value":5299650818.13},{"key":"19Q3","value":4056441877.54},{"key":"19Q2","value":2846117863.08}];
var mgsyChart = [{"key":"20Q3","value":0.23},{"key":"20Q2","value":0.13},{"key":"20Q1","value":0.07},{"key":"19Q4","value":0.24},{"key":"19Q3","value":0.19},{"key":"19Q2","value":0.11}];

var ylnlCharts1 = [{"key":"20Q3","value":["17.32"]},{"key":"20Q2","value":["15.00"]},{"key":"20Q1","value":["15.10"]},{"key":"19Q4","value":["14.04"]},{"key":"19Q3","value":["14.05"]},{"key":"19Q2","value":["11.63"]}];
var ylnlCharts2 = [{"key":"20Q3","value":["7.58"]},{"key":"20Q2","value":["4.37"]},{"key":"20Q1","value":["2.56"]},{"key":"19Q4","value":["8.66"]},{"key":"19Q3","value":["7.43"]},{"key":"19Q2","value":["4.34"]}];

var chnlCharts1 = [{"key":"20Q3","value":["0.95"]},{"key":"20Q2","value":["0.98"]},{"key":"20Q1","value":["1.09"]},{"key":"19Q4","value":["1.08"]},{"key":"19Q3","value":["0.71"]},{"key":"19Q2","value":["0.71"]}];
var chnlCharts2 = [{"key":"20Q3","value":["53.11"]},{"key":"20Q2","value":["54.98"]},{"key":"20Q1","value":["56.46"]},{"key":"19Q4","value":["56.42"]},{"key":"19Q3","value":["51.44"]},{"key":"19Q2","value":["53.72"]}];

var cznlCharts1 = [{"key":"20Q3","value":["19.71"]},{"key":"20Q2","value":["21.50"]},{"key":"20Q1","value":["0.53"]},{"key":"19Q4","value":["2.97"]},{"key":"19Q3","value":["-26.75"]},{"key":"19Q2","value":["-34.45"]}];
var cznlCharts2 = [{"key":"20Q3","value":["17.36"]},{"key":"20Q2","value":["19.78"]},{"key":"20Q1","value":["18.43"]},{"key":"19Q4","value":["19.21"]},{"key":"19Q3","value":["6.28"]},{"key":"19Q2","value":["6.98"]}];

var yynlCharts1 = [{"key":"20Q3","value":["3.92"]},{"key":"20Q2","value":["2.87"]},{"key":"20Q1","value":["1.63"]},{"key":"19Q4","value":["5.76"]},{"key":"19Q3","value":["48.30"]},{"key":"19Q2","value":["3.45"]}];
var yynlCharts2 = [{"key":"20Q3","value":["0.24"]},{"key":"20Q2","value":["0.15"]},{"key":"20Q1","value":["0.08"]},{"key":"19Q4","value":["0.34"]},{"key":"19Q3","value":["0.29"]},{"key":"19Q2","value":["0.20"]}];
</script>
    <script type="text/javascript">
var f2eConfig = {
	stockts: 'http://file.ws.126.net/f2e/finance/gegu/js/stock_ts_js.667271.swf',
	stockkl: 'http://file.ws.126.net/f2e/finance/gegu/js/stock_kl_js.667271.swf'
}

/*
function doTracker(){
	setTimeout(function(){if(typeof neteaseTracker == "function")neteaseTracker();doTracker();},5*60*1000);
} 
doTracker();
*/

// 二维码
!(function(){
	var version = window.navigator.appVersion;
	var isIE6 = (version.indexOf("MSIE 6.0") != -1 || version.indexOf("MSIE 5.5") != -1)? true:false;
	if(location.hostname.indexOf("news") == -1){
           showQR(35, "http://img4.cache.netease.com/stock/2017/5/24/20170524105815a8be1.png");
           // http://img2.cache.netease.com/stock/2014/8/14/20140814165055a7606.jpg
           //
           // http://img6.cache.netease.com/stock/2014/2/18/20140218110538d9103.jpg 微信易信二维码
           //
           // http://img2.cache.netease.com/stock/2014/10/21/201410211523115048d.png
		   // http://img1.cache.netease.com/stock/2014/11/26/201411261107570399d.png
           //
	}
	function showQR(bottom, imgUrl){
		var QRbox= document.createElement("div");
		var QRboxCSS ={
			'width': "110px",
			'height': "147px",
			'position': "fixed",
			'_position': "absolute",
			'bottom': bottom + "px",
			'right': "3px",
			'display':"block",
			'zIndex':100
		};
		for(var key in QRboxCSS){
			QRbox.style[key] = QRboxCSS[key];
		}
	 	if(isIE6){
	 		QRbox.style.position = "absolute";
	 	}

		//QRbox.innerHTML="<a href='javascript:;' target='_blank'></a>";
		QRbox.innerHTML="<a href='http://money.163.com/special/app_spread230/?tc01' target='_blank'></a>";
		var link =QRbox.getElementsByTagName("a")[0];
		var backgroundImage = "url(" + imgUrl + ")";
		var linkCSS = {
			'display' : "block",
			'width' : "100%",
			'height' : "100%",
			'backgroundImage' : backgroundImage,
			'backgroundPosition' : "0px 0px"
		};
		for(var key in linkCSS){
			link.style[key] = linkCSS[key]
		}
		document.body.appendChild(QRbox);
		var linkEventMap = {
			"mouseover": function(){
				link.style.backgroundPosition = "-110px 0px";
			},
			"mouseout": function(){
				link.style.backgroundPosition = "0px 0px";
			}
		}
		for(var evt in linkEventMap){
			var func = linkEventMap[evt];
			addEvent(evt, link, func);
		}
		// addEvent("scroll", window, function(){
		// 	if( getScrollTop() > 200 ){
		// 		QRbox.style.display = 'block';
		// 	}else{
		// 		QRbox.style.display = 'none';
		// 	}
		// 	if(isIE6){
		// 		QRbox.style.top = getScrollTop() + top + "px";
		// 	}
		// });
		var body = document.body;
		addEvent("resize", window, function(){
			var bodyWidth = body.clientWidth;
			if( bodyWidth < 1180 ){
				QRbox.style.right = (bodyWidth - 1180)/2 + 'px';
			}else{
				QRbox.style.right = '3px';
			}
		});
	}
	function addEvent(evt, elem, callback){
		if(elem.addEventListener){
			elem.addEventListener(evt, callback, false)
		} else {
			elem.attachEvent && elem.attachEvent("on"+evt, callback);
		}
	}
	function getScrollTop(){
	    if(typeof pageYOffset!= 'undefined'){
	        //most browsers
	        return pageYOffset;
	    }
	    else{
	        var B= document.body; //IE 'quirks'
	        var D= document.documentElement; //IE with doctype
	        D= (D.clientHeight)? D: B;
	        return D.scrollTop;
	    }
	}
})();

</script>
<script src="http://img1.cache.netease.com/f2e/lib/js/ne.js"></script>
<script src="http://img2.cache.netease.com/f2e/libs/jquery.js"></script>
<script src="http://img1.cache.netease.com/f2e/finance/gegu/js/ne_gegu_a.VxEO4twoqLvl.1.js"></script>
<script src="http://img1.cache.netease.com/f2e/finance/gegu/js/ne_gegu_b.jR2HPJ8AZpUI.1.js"></script>
    <script src="http://img1.cache.netease.com/f2e/finance/gegu/js/e.645958.min.js"></script>
    <div class="blank20"></div>
    <div class="foot">
<div class="text"><a href="http://money.163.com/special/zhubianmail/">主编信箱</a>　热线:010-82558752　<a href="http://money.163.com/10/1201/14/6MQU982O00251OB6.html">加入我们</a> <a href="http://fankui.163.com/ft/cq.fb?pid=10005" target="_blank">意见反馈</a>　</div>
<a href="http://corp.163.com/">About NetEase</a> - <a href="http://gb.corp.163.com/gb/about/overview.html">公司简介</a> - <a href="http://gb.corp.163.com/gb/contactus.html">联系方法</a> - <a href="http://corp.163.com/gb/job/job.html">招聘信息</a> - <a href="http://help.163.com/">客户服务</a> - <a href="http://gb.corp.163.com/gb/legal.html">隐私政策</a> - <a href="http://emarketing.biz.163.com/">网络营销</a> - <a href="http://sitemap.163.com/">网站地图</a> <br>
网易公司版权所有<br>
<span class="cRed">©1997-2021</span>
<div class="blank20"></div>
</div>
<!-- START WRating v1.0 -->
<script type="text/javascript" src="http://img6.cache.netease.com/common/script/wrating.js">
</script>
<script type="text/javascript">
var vjAcc="860010-0507010000";
var wrUrl="http://163.wrating.com/";
vjTrack("");
</script>
<noscript><img src="http://163.wrating.com/a.gif?a=&c=860010-0507010000" width="1" height="1"/></noscript>
<!-- END WRating v1.0 -->
<!-- START NetEase Devilfish 2006 -->
<script src="http://analytics.163.com/ntes.js" type="text/javascript"></script>
<script type="text/javascript">
_ntes_nacc = "stock";     //站点ID。
neteaseTracker();
neteaseClickStat();
</script>
<!-- END NetEase Devilfish 2006 -->
<!-- START monitor -->
<!-- END monitor -->
</div>
</body>
</html>
    """

    # soup = bs4.BeautifulSoup(s, "html5lib")
    # ss = soup.text

    # print(ss)

    # 遍历可转债列表
    # 打开文件数据库
    con_file = sqlite3.connect('../db/cb.db3')

    try:
        # 查询可转债

        bond_cursor = con_file.execute("""
            SELECT bond_code, cb_name_id, stock_code, stock_name from changed_bond
        """)

        i = 0
        for bond_row in bond_cursor:

            bond_code = bond_row[0]
            stock_code = bond_row[2]
            stock_name = bond_row[3]

            stock_cursor = con_file.execute("SELECT bond_code, stock_code, last_date from stock_report where bond_code = " + bond_code)

            earnings = getEarnings(stock_code)

            stocks = list(stock_cursor)
            # 还没添加股票信息
            if len(stocks) == 0:
                # 新增
                con_file.execute("""insert into stock_report(bond_code,cb_name_id,stock_code,stock_name,
                            last_date,
                            revenue,qoq_revenue_rate,yoy_revenue_rate,
                            net,qoq_net_rate,yoy_net_rate,
                            margin,qoq_margin_rate,yoy_margin_rate,
                            roe,qoq_roe_rate,yoy_roe_rate,
                            al_ratio,qoq_rl_ratio_rate,yoy_al_ratio_rate)
                         values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                 (bond_row[0], bond_row[1], bond_row[2], bond_row[3],
                                  earnings.lastDate,

                                  earnings.revenue,
                                  earnings.qoqRevenueRate,
                                  earnings.yoyRevenueRate,

                                  earnings.net,
                                  earnings.qoqNetRate,
                                  earnings.yoyNetRate,

                                  earnings.margin,
                                  earnings.qoqMarginRate,
                                  earnings.yoyMarginRate,

                                  earnings.roe,
                                  earnings.qoqRoeRate,
                                  earnings.yoyRoeRate,

                                  earnings.alRatio,
                                  earnings.qoqAlRatioRate,
                                  earnings.yoyAlRatioRate
                                  )
                                 )
                print("insert " + stock_name + " is successful")
            else:
                last_date = stocks[0][2]
                if last_date != earnings.lastDate:
                    con_file.execute("""update stock_report
                                set last_date = ?,
                                revenue = ?,qoq_revenue_rate = ?,yoy_revenue_rate = ?,
                                net = ?,qoq_net_rate = ?,yoy_net_rate = ?,
                                margin = ?,qoq_margin_rate = ?,yoy_margin_rate = ?,
                                roe = ?,qoq_roe_rate = ?,yoy_roe_rate = ?,
                                al_ratio = ?,qoq_rl_ratio_rate = ?,yoy_al_ratio_rate = ?
                             where bond_code = ?""",
                                     (earnings.lastDate,

                                      earnings.revenue,
                                      earnings.qoqRevenueRate,
                                      earnings.yoyRevenueRate,

                                      earnings.net,
                                      earnings.qoqNetRate,
                                      earnings.yoyNetRate,

                                      earnings.margin,
                                      earnings.qoqMarginRate,
                                      earnings.yoyMarginRate,

                                      earnings.roe,
                                      earnings.qoqRoeRate,
                                      earnings.yoyRoeRate,

                                      earnings.alRatio,
                                      earnings.qoqAlRatioRate,
                                      earnings.yoyAlRatioRate,

                                      bond_code
                                      )
                                     )
                    print("update " + stock_name + " is successful")

            # 暂停10s再执行， 避免被网站屏蔽掉
            time.sleep(10)
            i += 1

        print("共处理" + str(i) + "条记录")

    except Exception as e:
        con_file.close()
        print("db操作出现异常" + e, e)
    finally:
        con_file.commit()
        con_file.close()


def getEarnings(stock_code):
    url = "http://quotes.money.163.com/f10/zycwzb_" + stock_code + ".html#01c02"
    response = requests.get(url=url)
    # response = requests.get(url=url, headers=header)
    # print(response.text)

    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    soup = bs4.BeautifulSoup(response.text, "html5lib")

    # 报表区
    tables = soup.find_all('table', class_='table_bg001 border_box limit_sale scr_table')
    if len(tables) == 0:
        print("报表区发生变化，无法找到数据")

    trs = list(tables[0].tbody.children)

    earnings = Earnings()

    # 最近的报告期
    earnings.lastDate = list(trs[0].children)[1].text

    # 主营业务收入(万元)
    earnings.calcRevenue(list(trs[8].children))

    # 净利润(万元)
    earnings.calcNet(list(trs[20].children))

    # 利润率 = 主营业务利润(万元)/主营业务收入(万元)
    earnings.calcMargin()

    # 计算负债率
    earnings.calcAlRatio(list(trs[28].children), list(trs[32].children))

    # roe 净资产收益率加权(%)
    earnings.calcRoe(list(trs[38].children))

    # print(earnings)
    return earnings

def noConvert(val):
    return val

def convert(val):
    return round(val/10000, 4)

#每一条财报记录
class Record:
    # 当前报告期的值
    lastValue = 0
    # 上一年的值
    yoyValue = 0
    # 同比增长率
    yoyRate = 0

    # 前一个财报值
    preValue = 0

    # 当前季度值
    curQoqValue = 0
    # 前一个季度值
    preQoqValue = 0

    # 环比增长率
    qoqRate = 0

    def parseData(self, tds, convert=noConvert):
        # 最近的值
        self.lastValue = convert(float(tds[0].text.replace(',', '')))
        # 上一年的值
        self.yoyValue = convert(float(tds[4].text.replace(',', '')))
        # 同比增长率
        self.yoyRate = round((self.lastValue - self.yoyValue)*100 / self.yoyValue, 2)

        # 前一个财报值
        self.preValue = convert(float(tds[1].text.replace(',', '')))
        # 当前季度值
        self.curQoqValue = round(self.lastValue - self.preValue, 4)
        # 前前一个财报值
        prePreValue = convert(float(tds[2].text.replace(',', '')))
        # 前一个季度值
        self.preQoqValue = round(self.preValue - prePreValue, 4)

        # 环比增长率
        self.qoqRate = round((self.curQoqValue - self.preQoqValue)*100 / self.preQoqValue, 2)

# 财报信息
class Earnings:
    lastDate = ''
    # 营收
    revenue = 0
    # 当季
    curQoqRevenue = 0
    # 上一季
    preQoqRevenue = 0
    # 上一年
    yoyRevenue = 0
    # 环比
    qoqRevenueRate = 0
    # 同比
    yoyRevenueRate = 0

    def calcRevenue(self, tds):
        record = Record()
        record.parseData(tds, convert)
        self.revenue = record.lastValue
        self.curQoqRevenue = record.curQoqValue
        self.preQoqRevenue = record.preQoqValue
        self.yoyRevenue = record.yoyValue
        self.qoqRevenueRate = record.qoqRate
        self.yoyRevenueRate = record.yoyRate

    # 净利润
    net = 0
    # 当季
    curQoqNet = 0
    # 上季
    preQoqNet = 0
    # 上一年
    yoyNet = 0
    # 环比
    qoqNetRate = 0
    # 同比
    yoyNetRate = 0

    def calcNet(self, tds):
        record = Record()
        record.parseData(tds, convert)
        self.net = record.lastValue
        self.curQoqNet = record.curQoqValue
        self.preQoqNet = record.preQoqValue
        self.yoyNet = record.yoyValue
        self.qoqNetRate = record.qoqRate
        self.yoyNetRate = record.yoyRate

    # 利润率
    margin = 0
    # 当季
    curQoqMargin = 0
    # 上一季
    preQoqMargin = 0
    # 上一年
    yoyMargin = 0
    # 环比
    qoqMarginRate = 0
    # 同比
    yoyMarginRate = 0

    def calcMargin(self):
        self.margin = round(self.net * 100 / self.revenue, 2)

        # 当前季的利润率 = 当前季度利润/当前季度营收
        self.curQoqMargin = round(self.curQoqNet * 100 / self.curQoqRevenue, 2)
        # 上一季度利润率 = 上一季度利润/上一季度营收
        self.preQoqMargin = round(self.preQoqNet * 100 / self.preQoqRevenue, 2)

        # 环比 = (当前季 - 上一季)/上一季
        self.qoqMarginRate = round((self.curQoqMargin - self.preQoqMargin) * 100 / self.preQoqMargin, 2)

        # 上一年利润率 = 上一年利润/上一年营收
        self.yoyMargin = round(self.yoyNet * 100 / self.yoyRevenue, 2)
        # 同比 = (当前利润率 - 上一年利润率)/上一年利润率
        self.yoyMarginRate = round((self.margin - self.yoyMargin) * 100 / self.yoyMargin, 2)

    # 净资产收益率
    roe = 0
    # 环比
    qoqRoeRate = 0
    # 同比
    yoyRoeRate = 0

    def calcRoe(self, tds):
        record = Record()
        record.parseData(tds)
        self.roe = record.lastValue
        self.qoqRoeRate = record.qoqRate
        self.yoyRoeRate = record.yoyRate

    # 资产负债率
    alRatio = 0
    # 环比
    qoqAlRatioRate = 0
    # 同比
    yoyAlRatioRate = 0

    def calcAlRatio(self, assetsTds, debtTds):
        # 总资产
        record1 = Record()
        record1.parseData(assetsTds, convert)
        assets = record1.lastValue
        # 总负债
        record2 = Record()
        record2.parseData(debtTds, convert)
        debt = record2.lastValue

        #资产负债率
        self.alRatio = round(debt * 100 / assets, 2)

        #环比
        #当季负债率
        curQoqRatio = round(record2.curQoqValue * 100 / record1.curQoqValue, )
        #上季负债率
        preQoqRatio = round(record2.preQoqValue * 100 / record1.preQoqValue, 2)
        self.qoqAlRatioRate = round((curQoqRatio - preQoqRatio) * 100/preQoqRatio, 2)

        #同比
        #上一年
        yoyAlRatio = round(record2.yoyValue * 100 / record1.yoyValue, 2)
        self.yoyAlRatioRate = round((self.alRatio - yoyAlRatio) * 100 / yoyAlRatio, 2)

if __name__ == "__main__":
    # createDb()
    getContent()
