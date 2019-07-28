#!/usr/local/bin/python3
# encoding:utf-8
import requests
import base64
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import platform
import sys

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
    print('result_list: %s' % type(result_list))
    requests.post(api_url, headers=headers,verify=False, json=result_list)


def web_browser(browser, wait, task_id, target):
    browser.get('https://www.sogou.com/')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="stb"]')))
    print('browser_target: %s' % target)
    start_time = time.time()
    result = {}
    browser.get(target)
    if target == 'https://www.baidu.com':
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lh"]/a[3]')))
            #wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="su"]')))
            # wait.until(EC.element_to_be_clickable((By.ID, 'su')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://www.google.com':
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="tsf"]/div[2]/div/div[3]/center/input[1]')))
            # wait.until(EC.element_to_be_clickable((By.NAME, 'btnK')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://w3.ibm.com':
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app"]/div/div[1]/div/nav[2]/a/span')))
            # wait.until(EC.element_to_be_clickable((By.ID, 'termsLink')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://www.yahoo.com':
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="uh-search-button"]')))
            # wait.until(EC.element_to_be_clickable((By.ID, 'uh-search-button')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://www.ibm.com':
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="ibm-footer"]/div/div/div/ul/li[1]/a')))
            # wait.until(EC.element_to_be_clickable((By.ID, 'ibm-search')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://9.111.147.16':
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="username"]')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://ned100.cn.ibm.com:19002':
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/h1')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target == 'https://site.ip138.com':
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div/a[1]/img')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    elif target in ['http://9.111.147.142', 'http://9.111.147.121', 'http://9.111.147.122']:
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/h1')))
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    else:
        try:
            time.sleep(20)
            end_time = time.time()
            duration = end_time - start_time
        except:
            duration = -999
    print(target, ' duration: %s' % duration)
    pic_name = browser.get_screenshot_as_base64()
    result['target'] = target
    result['count'] = 0
    result['testType'] = 'browser'
    result['result'] = duration
    result['image'] = pic_name
    post_data_to_socketroom(task_id, result)
    # print(result_list)
    # save_result_to_redis(result)


def run_browser(params):
    target = params['target']
    task_id = params['task_id']
    system_version = platform.dist()[0]
    display = Display(visible=0, size=(800, 600))
    display.start()
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--allow-running-insecure-content')
    # chrome_options.add_argument('--disable-popup-blocking')
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('window-size=1600,900')
    capabilities = webdriver.DesiredCapabilities.CHROME.copy()
    capabilities['acceptSslCerts'] = True
    capabilities['acceptInsecureCerts'] = True
    if system_version == 'debian':
        try:
            browser = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', options=chrome_options)
        except:
            browser = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', options=chrome_options)
            print('**********************Exception: Chrome ERROR!!!***************************')
    elif system_version == 'redhat':
        try:
            browser = webdriver.Chrome(options=chrome_options)
        except:
            browser = webdriver.Chrome(options=chrome_options)
            print('**********************Exception: Chrome ERROR!!!***************************')
    wait = WebDriverWait(browser, 30)
    web_browser(browser, wait, task_id, target)
    browser.quit()
    # display.stop()


if __name__ == '__main__':
    args = sys.argv[1]
    args = args.replace("'", '"')
    args = json.loads(args)
    run_browser(args)
