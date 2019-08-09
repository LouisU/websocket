
def main():
    import os
    import selenium
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait
    import time
    from bs4 import BeautifulSoup
    from pyvirtualdisplay import Display
    import socket
    import requests
    import json

    def post_data_to_socketroom(room, data):
        json_data = {
            "webex": data,
            "room": room
        }
        requests.post('https://ned100.cn.ibm.com:4433/webex', data=json.dumps(json_data), verify=False)

    #******************************format time start ******************************************
    interval = 5  # 5 minute
    now = time.time()
    now_timeslot = now // (interval * 60) * (interval * 60)
    now_display = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_timeslot))
    dtime = now_display
    unix_time = float(now_timeslot)
    # ******************************format time end ******************************************
    display = Display(visible=0, size=(800,600))
    display.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('window-size=1600,900')
    browser = webdriver.Chrome(options=options)
    wait = WebDriverWait(browser, 1000)
    url = "https://mediatest.ciscospark.com/#/main"
    browser.get(url)
    start_test = wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="start_tests"]')))
    start_test.click()
    copy_result = wait.until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div[3]/div[2]/div/div/article/div[5]/div/a[2]')))
    copy_result.click()
    more_details = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[2]/div/div/article/div[5]/div/a[3]')))
    more_details.click()
    html = browser.page_source
    browser.quit()
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table', class_='result-table').find_all('td')
    json_data = {
        'unix_time': unix_time,
        'dtime': dtime,
        'version': table[3].text,
        'browser': table[5].text,
        'result': 'Finished',
        'app': table[26].text,
        'room_system': table[28].text,
        'call': table[30].text,
        'network_connection': table[32].text,
        'public_ip_addr': table[34].text,
        'tcp_connection_tests': table[36].text,
        'tcp_delay': table[38].text,
        'tcp_download_speed': table[40].text,
        'tcp_upload_speed': table[42].text,
        'udp_connection_tests': table[44].text,
        'udp_delay': table[46].text,
        'udp_download_lossrate': table[52].text,
        'udp_upload_lossrate': table[54].text,
        'udp_download_jitter': table[48].text,
        'udp_upload_jitter': table[50].text,
        'udp_download_speed': table[56].text,
        'udp_upload_speed': table[58].text,
        'client_ip': os.environ.get('HOST_IP')
    }

    print(json_data)
    print(requests.post('https://ned83.cn.ibm.com/api/v2/current/webex_spark/', verify=False, json=json_data).content)
    post_data_to_socketroom('webex_spark', json_data)

