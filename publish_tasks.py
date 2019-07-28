from beacon.libs.celery import AsyncTask
import time
import sys
from io import StringIO

loop = int(sys.argv[1])

s = StringIO()

code = '''
def add_func():
    return 1+1
func = add_func
'''
s.write(time.ctime()+"\n")
for i in range(loop):
    task = AsyncTask.apply_async(kwargs={'code': code, 'kwargs':{}}, queue='louis')
    if i == 0:
        task_first = task
    elif i == loop - 1:
        task_last = task

s.write(time.ctime()+"\n")


while True:
    if task_last.state == "SUCCESS":
        s.write(task_first.result['time']+"\n")
        s.write(task_last.result['time'])
        print(s.getvalue())
        break
    else:
        time.sleep(1)


# def sync_request(url,index=0):
#     global result
#     with requests.Session() as session:
#         #print(url)
#         with session.get(url,verify=False,timeout=30) as response:
#             status=response.status_code
#             if status==200:
#                 html=response.text
#                 print(index,url,status,len(html),time.time() - start)
#             else:
#                 print('{}被阻止，状态码：'.format(url), resp.status)
#         web[url]={'status:':status,'html':html}
#         return url,status,html