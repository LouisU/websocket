#encoding:utf-8

def main():
    import requests
    from lxml import etree
    import time
    import xlrd
    #******************************format time start ******************************************
    interval = 5  # 5 minute
    now = time.time();
    now_timeslot = now // (interval * 60) * (interval * 60)
    now_display = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_timeslot))
    dtime = now_display
    NowTime = now_timeslot
    # ******************************format time end ******************************************
    login_url = 'http://net-monitor.chinatelecomglobal.com/Orion/Login.aspx?autologin=no'
    headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        }
    FormData = {'ctl00$BodyContent$Username': 'ibm',
                'ctl00$BodyContent$Password': 'ibm2015',
                '__EVENTTARGET': 'ctl00$BodyContent$ctl04',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': '17lV/iyGBIwOY+cTpGsCHQs3RxFG4sgPhtP19XBD27w99P2ns5EvUnmmWLjmN69UrU8TAz5yJ3rrDwE0W2qS3WqAP1QAXoK98CNNvxXdN0sYj4+r50ACpKNhun2/5LEEx/tVoNindF6lPUnjtAvYbduwk2fz+H2VERC4eySM4XhC8Akfu5UxlwgJoDEfqrUyy2vl9pG7DiY6GHaKqbdSdhR4xZRF7RCq/aFQM2l9KHL3ztahb6xGTo6rNJnxjCJBOJRiTX5Estjg6Se3Ny1UYWOhvrYSYIhnLw/fkb7OjynLCdW8TPlBM86cnesTbipxKPUL8bkgxRbdlZDKFdNa7uPOWDwgij5CKWMBCNtKwJ1hiwBjmw6x9/HUicQXOOJfshpKM2ALv29qPwSLNpRVYHLu8i2r8QX0OiI3Q2YMM1Y6ctSGAPxHyCTSB+IBXJeDR0cqtwHPDZFVl9rtJdcFnav4J0AnPylhvg7IO4ZvZFT6WG9si6OpEBqA/DPCxbM7',
                }
    S = requests.Session()
    S.verify = False
    S.headers = headers
    req = S.post(login_url, data=FormData)
    Response = (S.get('http://net-monitor.chinatelecomglobal.com/Orion/DetachResource.aspx?ResourceID=1194&NetObject=&currentUrl=aHR0cDovL25ldC1tb25pdG9yLmNoaW5hdGVsZWNvbWdsb2JhbC5jb20vT3Jpb24vU3VtbWFyeVZpZXcuYXNweA%3d%3d'))
    table_html = Response.content
    selector = etree.HTML(table_html)

    #CU Part                    ‘//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl01_VolumePercerUseLink1"]’
    CU_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl06_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    CU_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl06_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    CU_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl06_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    CU_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl06_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    Backup_CU_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl09_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    Backup_CU_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl09_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    Backup_CU_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl09_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    Backup_CU_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl09_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    CU = [NowTime,dtime,'CU',CU_RX_UTL,CU_RX_UTL_Percent,CU_TX_UTL,CU_TX_UTL_Percent,Backup_CU_RX_UTL,Backup_CU_RX_UTL_Percent,Backup_CU_TX_UTL,Backup_CU_TX_UTL_Percent]
    for i in range(3, len(CU)):
        VALUE = " ".join(CU[i].split())
        CU[i] = float((VALUE.split(' '))[0])
        X = (VALUE.split(' '))[1]
        if X == 'Mbps':
            CU[i] = CU[i]*1024*1024
        if X == 'Gbps':
            CU[i] = CU[i] * 1024 * 1024 * 1024

    #CT4809 Part
    CT4809_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl17_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    CT4809_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl17_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    CT4809_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl17_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    CT4809_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl17_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    Backup_CT4809_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl13_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    Backup_CT4809_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl13_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    Backup_CT4809_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl13_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    Backup_CT4809_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl13_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    CT4809 = [NowTime,dtime,'CT4809',CT4809_RX_UTL,CT4809_RX_UTL_Percent,CT4809_TX_UTL,CT4809_TX_UTL_Percent,Backup_CT4809_RX_UTL,Backup_CT4809_RX_UTL_Percent,Backup_CT4809_TX_UTL,Backup_CT4809_TX_UTL_Percent]
    for i in range(3, len(CT4809)):
        VALUE = " ".join(CT4809[i].split())
        CT4809[i] = float((VALUE.split(' '))[0])
        X = (VALUE.split(' '))[1]
        if X == 'Mbps':
            CT4809[i] = CT4809[i]*1024*1024

    #CTSDN Part

    CTSDN_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl18_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    CTSDN_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl18_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    CTSDN_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl18_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    CTSDN_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl18_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    Backup_CTSDN_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl14_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    Backup_CTSDN_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl14_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    Backup_CTSDN_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl14_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    Backup_CTSDN_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl14_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()

    CTSDN = [NowTime,dtime,'CTSDN',CTSDN_RX_UTL,CTSDN_RX_UTL_Percent,CTSDN_TX_UTL,CTSDN_TX_UTL_Percent,Backup_CTSDN_RX_UTL,Backup_CTSDN_RX_UTL_Percent,Backup_CTSDN_TX_UTL,Backup_CTSDN_TX_UTL_Percent]
    for i in range(3, len(CTSDN)):
        VALUE = " ".join(CTSDN[i].split())
        CTSDN[i] = float((VALUE.split(' '))[0])
        X = (VALUE.split(' '))[1]
        if X == 'Mbps':
            CTSDN[i] = CTSDN[i]*1024*1024

    #CM_SDN
    CM_SDN_RX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl03_VolumePercerUseLink1"]'))[0].xpath('string(.)').strip()
    CM_SDN_RX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl03_VolumePercerUseLink2"]'))[0].xpath('string(.)').strip()
    CM_SDN_TX_UTL = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl03_VolumePercerUseLink3"]'))[0].xpath('string(.)').strip()
    CM_SDN_TX_UTL_Percent = (selector.xpath('//*[@id="ctl00_BodyContent_ctl01_ctl00_ResourceWrapper_NodesRepeater_ctl03_VolumePercerUseLink4"]'))[0].xpath('string(.)').strip()
    Backup_CM_SDN_RX_UTL = '0 Mbps'
    Backup_CM_SDN_RX_UTL_Percent = '0 %'
    Backup_CM_SDN_TX_UTL = '0 Mbps'
    Backup_CM_SDN_TX_UTL_Percent = '0 %'

    CM_SDN = [NowTime,dtime,'CM_SDN',CM_SDN_RX_UTL,CM_SDN_RX_UTL_Percent,CM_SDN_TX_UTL,CM_SDN_TX_UTL_Percent,Backup_CM_SDN_RX_UTL,Backup_CM_SDN_RX_UTL_Percent,Backup_CM_SDN_TX_UTL,Backup_CM_SDN_TX_UTL_Percent]
    for i in range(3, len(CM_SDN)):
        VALUE = " ".join(CM_SDN[i].split())
        CM_SDN[i] = float((VALUE.split(' '))[0])
        X = (VALUE.split(' '))[1]
        if X == 'Mbps':
            CM_SDN[i] = CM_SDN[i]*1024*1024


    raw_data = [tuple(CU), tuple(CT4809), tuple(CTSDN), tuple(CM_SDN)]
    # raw_data = [tuple(CU), tuple(CT4809), tuple(CTSDN)]
    direction_list = ['inbound','outbound']
    for row in raw_data :
        dict = {}
        dict['circuit_name'] = row[2]
        dict['date'] = row[1][0:10]
        dict['unix_time'] = row[0]
        dict['pri_rx_utl'] = row[3]
        dict['pri_tx_utl'] = row[5]
        # print dict
        date = dict['date']
        unix_time = str(row[0]) +'0000'
        print("unix_time %s")%unix_time
        for direction in direction_list:
            url = 'https://ned83.cn.ibm.com/api/v2/current/demo3_site_isp_util/?date='+date+'&direction='+direction+'&circuit_name='+row[2]+''
            requests.packages.urllib3.disable_warnings()
            r = requests.get(url,verify=False)
            # print eval(r.content)['ret']
            # has this date data
            if eval(r.content)['ret'] == 'failed' :
                url_post = 'https://ned83.cn.ibm.com/api/v2/current/demo3_site_isp_util/'
                dict_outbound = {}
                dict_inbound = {}
                dict_inbound['circuit_name'] = row[2]
                dict_inbound['date'] = row[1][0:10]
                dict_inbound['data'] = {}
                dict_inbound['data'][unix_time] = row[3]
                dict_inbound['direction'] = 'inbound'

                dict_outbound['circuit_name'] = row[2]
                dict_outbound['date'] = row[1][0:10]
                dict_outbound['data'] = {}
                dict_outbound['data'][unix_time] = row[5]
                dict_outbound['direction'] = 'outbound'

                r_inbound = requests.post(url_post,json=dict_inbound,verify=False)
                r_outbound = requests.post(url_post,json=dict_outbound,verify=False)
                print(r_inbound.content,r_outbound.content)
            else :
                redis_data = eval(r.content)['data']
                for key in redis_data:
                    if redis_data[key]['direction'] == 'inbound':
                        redis_data[key]['data'] = eval(redis_data[key]['data'])
                        redis_data[key]['data'][unix_time] = row[3]
                    elif redis_data[key]['direction'] == 'outbound':
                        redis_data[key]['data'] = eval(redis_data[key]['data'])
                        redis_data[key]['data'][unix_time] = row[5]
                    url = 'https://ned83.cn.ibm.com/api/v2/current/demo3_site_isp_util/'
                    r = requests.post(url,json=redis_data[key],verify=False)
                    print(r.content)


main()