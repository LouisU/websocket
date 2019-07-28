#!/usr/local/bin/python
import time
import requests
import json
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from subprocess import PIPE, Popen, STDOUT
import sys

def ping_host(task_id, target, count):
    ping_target = target
    ping_count = 1
    ping_timeout = 1
    ping_deadline = ping_timeout * ping_count
    ping_cmd = '/bin/ping -c%d -W%d -w%d -A -q %s' % (
        ping_count, ping_timeout, ping_deadline, ping_target)
    # print(ping_cmd)
    try:
        result = {}
        p = Popen(ping_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        out = str(p.communicate()[0]).split('\n')
        if len(out) >= 1:
            if out[0]:
                roundtrip_stat = out[0].split(
                    ' = ')[1].split(' ms')[0].split('/')
                result[count] = float(roundtrip_stat[2])
            else:
                result[count] = -999
        else:
            result[count] = -999
    except Exception as e:
        result[count] = -999
    if count == 9:
        result['status'] = 'done'
    else:
        result['status'] = 'in progress'
    result_dict = {"testType":"ping", "target":target, "count":count, "result":result[count]}
    print(result_dict)
    post_data_to_socketroom(task_id, result_dict)
    save_result_to_redis(result_dict)

def post_data_to_socketroom(task_id, data):
    json_data = {
        "webex": data,
        "room": task_id
    }
    requests.post('https://ned100.cn.ibm.com:4433/webex', data=json.dumps(json_data), verify=False)


def save_result_to_redis(result_list):
    api_url = 'https://ned100.cn.ibm.com:49000/uat/save_result2'
    headers = {}
    method = 'post'
    headers["Accept"] = "application/json"
    if method.upper() in ['POST', "PATCH", "PUT"]:
        headers["Content-Type"] = "application/json"
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    session.request(method, api_url, headers=headers,
                    verify=False, data=json.dumps(result_list))


def ping(params):
    target = params['target']
    task_id = params['task_id']
    init_task = {'target': target, 'testType': 'ping'}
    post_data_to_socketroom(task_id, init_task)
    for count in range(10):
        ping_host(task_id, target, count)


if __name__ == '__main__':
    args = sys.argv[1]
    args = args.replace("'", '"')
    args = json.loads(args)
    ping(args)