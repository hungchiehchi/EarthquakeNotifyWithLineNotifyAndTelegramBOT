import sys
import traceback
import numpy as np
import cv2
import win32gui
import win32con
import win32ui
import re
from time import sleep

import requests

def send_telegram_notification(chat_id, token, magnitude, second):
    # 傳送訊息
    url = f"https://api.telegram.org/{token}/sendMessage"
    message= f"⚠️地震速報⚠️ <b>{second}秒</b> 後 <b>{magnitude}級</b> 地震將抵達 <b>台中</b> ，請注意安全。"
    params = {
        'chat_id': chat_id, 
        'text': message, 
        'parse_mode': 'HTML'
    }
    requests.post(url, params=params)

    #傳送圖片
    send_photo_url = f'https://api.telegram.org/{token}/sendPhoto'
    image = open('./wakeup.jpg', 'rb')
    files = {'photo': image}
    data  = {'chat_id': chat_id}
    requests.post(send_photo_url, files=files, data=data)

def send_line_notification(line_token, magnitude, second):
    # 參考 https://yhhuang1966.blogspot.com/2022/07/python-line-notify_2.html
    headers = {
        "Authorization": "Bearer " + line_token,
    }
    message = f" \n {second}秒 後 {magnitude}級 地震將抵達 台中 ，\n請注意安全。"

    image = open('./wakeup.jpg', 'rb')
    
    data = {
        'message': message,
    }

    imageFile = {
        'imageFile': image,
    }
    	
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data, files=imageFile)

def FindWindow_bySearch(pattern):
    window_list = []
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), window_list)
    for each in window_list:
        if re.search(pattern, win32gui.GetWindowText(each)) is not None:
            return each

def getWindow_W_H(hwnd):
    # 取得目標視窗的大小
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    width = right - left - 15
    height = bot - top - 11
    return (left, top, width, height)

def getWindow_Img(hwnd):
    # 將 hwnd 換成 WindowLong
    s = win32gui.GetWindowLong(hwnd,win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, s|win32con.WS_EX_LAYERED)
    # 判斷視窗是否最小化
    show = win32gui.IsIconic(hwnd)
    # 將視窗圖層屬性改變成透明    
    # 還原視窗並拉到最前方
    # 取消最大小化動畫
    # 取得視窗寬高
    if show == 1: 
        win32gui.SystemParametersInfo(win32con.SPI_SETANIMATION, 0)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_ALPHA)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)    
        x, y, width, height = getWindow_W_H(hwnd)        
    # 創造輸出圖層
    hwindc = win32gui.GetWindowDC(hwnd)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    # 取得視窗寬高
    x, y, width, height = getWindow_W_H(hwnd)
    # 如果視窗最小化，則移到Z軸最下方
    if show == 1: win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, x, y, width, height, win32con.SWP_NOACTIVATE)
    # 複製目標圖層，貼上到 bmp
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0 , 0), (width, height), srcdc, (8, 3), win32con.SRCCOPY)
    # 將 bitmap 轉換成 np
    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4) #png，具有透明度的
    # 釋放device content
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())
    # 還原目標屬性
    if show == 1 :
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
        win32gui.SystemParametersInfo(win32con.SPI_SETANIMATION, 1)
    # 回傳圖片
    return img

try:
    chat_id = "telegram_chat_id" # Telegram 頻道 id
    token = 'telegram_bot_token' # Telegram bot token

    # Line notify token
    line_tokens = ['line_notify_token']

    magnitude = str(sys.argv[1]).replace("+","強").replace("-","弱")
    second = int(sys.argv[2])

    # 視窗截圖
    hwnd = FindWindow_bySearch("地牛Wake Up!")
    frame = getWindow_Img(hwnd)
    cv2.imshow("screen box", frame)
    cv2.imwrite('wakeup.jpg', frame)
    # Telegram 通知
    send_telegram_notification(chat_id, token, magnitude, second)

    # Line 通知
    for line_token in line_tokens:
        status_code = send_line_notification(line_token, magnitude, second)
        print('status_code = {}'.format(status_code))

except Exception as e:
    with open("record_earth.txt","a", encoding='utf-8') as a:
        a.write(str(traceback.format_exc()))