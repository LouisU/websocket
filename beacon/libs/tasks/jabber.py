import pyautogui
import os
import sys
import time


CALL_NUMBER = sys.argv[1]
CALL_TIME = int(sys.argv[2])
print(CALL_NUMBER)
print(CALL_TIME)


def operate_jabber(number, time_s):
    # Open Jabber
    os.popen("open /Applications/Cisco\ Jabber.app")

    time.sleep(10)

    pyautogui.keyDown('shiftleft')
    pyautogui.press('tab')
    pyautogui.keyUp('shiftleft')

    time.sleep(1)
    # '*869915699'
    pyautogui.typewrite(number, 0.25)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(time_s)
    # pyautogui.keyDown('command')
    # pyautogui.press('q')
    # pyautogui.keyUp('command')
    # time.sleep(1)
    # pyautogui.press('enter')
    return 'DONE'

func = operate_jabber

if __name__ == "__main__":
    operate_jabber(CALL_NUMBER, CALL_TIME)