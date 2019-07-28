#encoding:utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

def main():
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--allow-running-insecure-content')
    # options.add_argument('--disable-popup-blocking')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('window-size=1366,768')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--use-fake-ui-for-media-stream')
    options.add_argument('--use-fake-device-for-media-stream')
    options.add_argument('--use-file-for-fake-audio-capture=/webex_demo/1.wav')
    options.add_argument('--use-file-for-fake-video-capture=/webex_demo/1.mjpeg')
    options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_camera": 1})
    options.add_argument('--ignore-certificate-errors')
    capabilities = webdriver.DesiredCapabilities.CHROME.copy()
    capabilities['acceptSslCerts'] = True
    capabilities['acceptInsecureCerts'] = True
    browser = webdriver.Chrome(chrome_options=options, desired_capabilities=capabilities)
    wait = WebDriverWait(browser, 300)
    browser.get('https://ibm.webex.com/mw3300/mywebex/cmr/cmr.do?siteurl=ibm&AT=meet&username=joe.liang')
    print('Title: %s' % browser.title)
    username = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="attendeeName"]')))
    username.send_keys('abc')
    email = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="attendeeEmail"]')))
    email.send_keys('test@test.com')
    time.sleep(5)
    email.send_keys(Keys.ENTER)
    start_time = time.time()
    wait.until(EC.title_is('Meeting is in progress...'))
    print('Title: %s' % browser.title)
    browser.switch_to_frame('pbui_iframe')
    conn_audio_video = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="oneclick_dlg_content"]/div/div[1]/div[2]/button[1]')))
    print(conn_audio_video)
    conn_audio_video.click()
    host = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="pb_layout"]/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div/div[5]/div/h3/span[3]')))
    print(host.text)
    participents = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="plist_control_btn"]')))
    participents.click()
    end_time = time.time()
    running_time = end_time - start_time
    print('running_time: %s' % running_time)
    time.sleep(600)
    browser.quit()


if __name__ == '__main__':
    main()
