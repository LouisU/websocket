#!/usr/bin/env python
#encoding:utf-8


def main():
    # from urlparse import urlparse
    import base64
    import logging
    # import httplib
    import http.client
    import json
    import time
    import sys
    import ssl
    import pandas as pd
    import sqlite3
    import datetime
    import re
    import numpy as np
    import pandas as pd
    from pandas import DataFrame
    import requests

    class SteelCentral():
        def __init__(self, url, HOST, BASIC_AUTH, start_time, end_time, return_rows):
            self.url = url
            self.HOST = HOST
            self.BASIC_AUTH = BASIC_AUTH
            self.start_time = start_time
            self.end_time = end_time
            self.return_rows = return_rows

        def Post_Data(self):
            # ******************************format time start ******************************************
            interval = 5  # 5 minute
            now = time.time();
            now_timeslot = now // (interval * 60) * (interval * 60)
            now_display = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_timeslot))
            dtime = now_display
            NowTime = now_timeslot
            print(dtime)
            print(NowTime)
            interfaces_name1 = ["interface CNBEIP9E2Y--01R.wan:TenGigabitEthernet0/1/0.100010"]
            interfaces_name = 'set any %s' % interfaces_name1
            # subnets = ['64.68.96.0/19','66.114.160.0/20','66.163.32.0/19','114.29.192.0/19','173.39.224.0/19','173.243.0.0/20','207.182.160.0/19','209.197.192.0/19','216.151.128.0/19','210.4.192.0/20','69.26.176.0/20']
            subnets = "64.68.96.10"
            Utl_report_post_data = {
                "criteria": {
                    "time_frame": {
                        "start": self.start_time,
                        "end": self.end_time
                    },
                    "queries": []
                },
                "template_id": 184
            }
            query_utilization = {
                "realm": "traffic_summary",
                "group_by": "por",
                # "traffic_expression": 'interface CNBEIP9E2Y--01R.wan:CH42_BJDC_Dom_Pri_Link and app Webex_RTP',
                "traffic_expression": 'interface CNBEIP9E2Y--01R.wan:CH42_BJDC_Dom_Pri_Link and  hostgroup ByFunction:WebEx_Media_Server',
                "columns": [3, 20, 33, 79, 88, 34, 556, 559, 560, 36, 82, 91, 532, 280, 32, 526, 30, 76, 85, 450, 451,
                            452, 460, 461, 462, 281, 934, 936, 939, 612, 282, 548],
                "sort_column": 33
            }
            # Utl_report_post_data["criteria"]["queries"].append(query_utilization1)
            Utl_report_post_data["criteria"]["queries"].append(query_utilization)
            report_list = Utl_report_post_data
            self.to_post = json.dumps(report_list)
            self.columns = []
            for col in report_list["criteria"]["queries"]:
                self.columns.append(col["columns"])
            self.output, info = SteelCentral.Do_Post(self)
            if (info['status'] is not 201):
                print("Unable to run report")
                sys.exit(1)
            self.location = SteelCentral.Get_Header(self, info['headers'], 'location')
            print("")
            print("Generated: %s") % self.location
            status_url = "https://%s%s.json" % (self.HOST, self.location)
            print("Please wait")
            while (True):
                output, info = SteelCentral.Do_GET(self, status_url)
                s = json.loads(output)
                print("Percent completed %s, seconds remaining %s...") % (s["percent"], s["remaining_seconds"])
                if (s["status"] == "completed"):
                    print("Completed")
                    break
                time.sleep(1)
            queries_url = "https://%s%s/queries.json" % (self.HOST, self.location)
            output, info = SteelCentral.Do_GET(self, queries_url)
            queries = json.loads(output)
            for k in range(0, len(queries)):
                query_id = queries[k]['id']
                columns_str = ','.join([repr(i) for i in self.columns[k]])
                data_url = "https://%s%s/queries/%s.json?offset=0&limit=%d&columns=%s" % (
                    self.HOST, self.location, query_id, self.return_rows, columns_str)
                output, info = SteelCentral.Do_GET(self, data_url)
                data = json.loads(output)
                # print 'data = %s' % data
                util_data1 = list(data['data'])
                data_ = []
                for i in range(len(util_data1)):
                    sub_util_data = []
                    for j in range(len(util_data1[i])):
                        if j < 3:
                            sub_util_data.append(str(util_data1[i][j]))
                            continue
                        if util_data1[i][j] == '':
                            sub_util_data.append(0)
                            continue
                        sub_util_data.append(float(util_data1[i][j]))
                    data_.append(sub_util_data)
                data_matrix = pd.DataFrame(data_)
                data_matrix.columns = ['Protocol', 'Port', 'Avg Bytes/s', 'Avg Bytes/s (Rx)', 'Avg Bytes/s (Tx)',
                                       'Avg Packets/s', 'Avg Bytes/s per Conn', 'Avg Bytes/s per Conn (Rx)',
                                       'Avg Bytes/s per Conn (Tx)', 'Peak Bytes/s', 'Peak Bytes/s (Rx)',
                                       'Peak Bytes/s (Tx)', 'Avg Active Connections/s', 'Avg Net RTT (ms)',
                                       'Total New Connections', 'Total Active Connections', 'Total Bytes',
                                       'TOTAL_BYTES_RX',
                                       'TOTAL_BYTES_TX', '% Retrans Bytes', '% Retrans Bytes (Rx)',
                                       '% Retrans Bytes (Tx)',
                                       '% Resets', '% Resets (Rx)', '% Resets (Tx)', 'Avg Resp Time (ms)',
                                       'Avg Req Network Time (ms)', 'Avg Resp Network Time (ms)',
                                       'Avg Total Transaction Time (ms)', 'Avg Client Delay (ms)',
                                       'Avg Server Delay (ms)',
                                       'Avg Conn Duration']

                # print data_matrix
                data_matrix.insert(0, 'DTime', 3, allow_duplicates=False)
                data_matrix.insert(0, 'unix_time', 3, allow_duplicates=False)
                data_matrix['DTime'] = dtime
                data_matrix['unix_time'] = NowTime
                # data_matrix.to_excel('webex.xlsx')

                # db2 operate
                temp_data = np.array(data_matrix)
                data_list = temp_data.tolist()
                print("data_list = %s") % data_list

                # post data to redis
                dict = {}
                url = 'https://ned83.cn.ibm.com/api/v2/current/demo3_webex_test/'
                requests.packages.urllib3.disable_warnings()
                for row in data_list:
                    dict['port'] = row[3]
                    dict['total_active_connections'] = row[17]
                    dict['total_bytes'] = row[18]
                    dict['unix_time'] = str(row[0]) + '0000'
                    print(dict)
                    r = requests.post(url, json=dict, verify=False)
                    print(r.content.decode())
                # db_name = 'DATABASE=DB_BOARD;HOSTNAME=9.94.82.30;PORT=50001;PROTOCOL=TCPIP;UID=db2icomm;PWD=db2icomm;'
                # table_name = 'WEBEX_PERF'
                # table = sql_table(db_name,table_name,db_type='db2')
                # table.structure = (0{'field': 'unix_time', 'type': 'decimal(15,5)'},
                #                    1{'field': 'dtime', 'type': 'VARCHAR(255)'},
                #                    2{'field': 'Protocol', 'type': 'DECIMAL(15,0)'},
                #                    3{'field': 'Port', 'type': 'VARCHAR(255)'},
                #                    4{'field': 'Avg_Bytes', 'type': 'DECIMAL(15,5)'},
                #                    5{'field': 'avg_bytes_rx', 'type': 'decimal(15,2)'},
                #                    6{'field': 'avg_bytes_tx', 'type': 'decimal(15,2)'},
                #                    7{'field': 'Avg_Packets', 'type': 'DECIMAL(15,5)'},
                #                    8{'field': 'avg_bytes_per_conn', 'type': 'decimal(15,2)'},
                #                    9{'field': 'avg_bytes_per_conn_rx', 'type': 'decimal(15,2)'},
                #                    10{'field': 'avg_bytes_per_conn_tx', 'type': 'decimal(15,2)'},
                #                    11{'field': 'peak_bytes', 'type': 'decimal(15,2)'},
                #                    12{'field': 'peak_bytes_rx', 'type': 'decimal(15,2)'},
                #                    13{'field': 'peak_bytes_tx', 'type': 'decimal(15,2)'},
                #                    4{'field': 'Avg_Active_Connections', 'type': 'DECIMAL(15,5)'},
                #                    5{'field': 'Avg_Net_RTT', 'type': 'DECIMAL(15,5)'},
                #                    6{'field': 'Total_New_Connections', 'type': 'DECIMAL(15,5)'},
                #                    7{'field': 'Total_Active_Connections', 'type': 'DECIMAL(15,5)'},
                #                    8{'field': 'total_bytes', 'type': 'decimal(15,2)'},
                #                    9{'field': 'total_bytes_rx', 'type': 'decimal(15,2)'},
                #                    {'field': 'total_bytes_tx', 'type': 'decimal(15,2)'},
                #                    {'field': 'retrans_bytes', 'type': 'decimal(15, 2)'},
                #                    {'field': 'retrans_bytes_rx', 'type': 'decimal(15,2)'},
                #                    {'field': 'retrans_bytes_tx', 'type': 'decimal(15,2)'},
                #                    {'field': 'resets', 'type': 'decimal(15,2)'},
                #                    {'field': 'resets_rx', 'type': 'decimal(15,2)'},
                #                    {'field': 'resets_tx', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_resp_time', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_req_network_time', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_resp_network_time', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_total_transaction_time', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_client_delay', 'type': 'decimal(15,2)'},
                #                    {'field': 'avg_server_delay', 'type': 'decimal(15, 2)'},
                #                    {'field': 'avg_conn_duration', 'type': 'decimal(15,2)'})
                # table.create()
                # table.insert(data_list)

        def Do_Post(self):
            self.conn = http.client.HTTPSConnection(self.HOST, 443)
            headers = {"Authorization": "Basic %s" % base64.b64encode(self.BASIC_AUTH.encode()),
                       "Content-Length": str(len(self.to_post)),
                       "Content-Type": "application/json"}
            self.conn.request('POST', self.url, body=self.to_post, headers=headers)
            res = self.conn.getresponse()
            info = {"status": res.status,
                    "headers": res.getheaders()}
            data = res.read()
            self.conn.close()
            return data, info

        def Get_Header(self, headers, header):
            for i in headers:
                if (i[0] == header):
                    return i[1]
            return ""

        def Do_GET(self, url):
            conn = http.client.HTTPSConnection(self.HOST, 443)
            headers = {"Authorization": "Basic %s" % base64.b64encode(self.BASIC_AUTH),
                       "Content-Length": 0,
                       "Content-Type": "application/json"}
            conn.request('GET', url, body="", headers=headers)
            res = conn.getresponse()
            info = {"status": res.status,
                    "headers": res.getheaders()}
            data = res.read()
            conn.close()
            return data, info
    ssl._create_default_https_context = ssl._create_unverified_context
    HOST = 'bld-wx-pfui.boulder.ibm.com'
    BASIC_AUTH = 'bezhumin:Welc0me!111111'
    # BASIC_AUTH = 'zhujianc:2wsx#EDC'
    url = "https://%s/api/profiler/1.1/reporting/reports.json" % HOST
    end_time = int(time.time() - 3 * 60)
    start_time = int(end_time - 5 * 60)
    return_rows = 200
    S = SteelCentral(url, HOST, BASIC_AUTH, start_time, end_time, return_rows)
    S.Post_Data()
