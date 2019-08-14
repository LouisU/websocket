from __future__ import absolute_import, unicode_literals
from celery import Celery, Task
from celery.schedules import crontab
import re
from celery.signals import after_task_publish, \
    before_task_publish, task_prerun, task_postrun, \
    eventlet_pool_apply, user_preload_options, celeryd_after_setup, \
    celeryd_init, worker_init, worker_ready, heartbeat_sent, worker_shutting_down,\
    worker_process_init, worker_process_shutdown, worker_shutdown
from os import path
import time
from .console import WorkerInfo
import requests
import json


celery_app = Celery('celery_app')
celery_app.config_from_object('beacon.config')


# send worker logs into rabbitmq
def sender(message):
    publisher = WorkerInfo()
    publisher.publish(message)


class _AsyncTask(Task):
    """
    usage: AsyncTask.apply_async(kwargs={'id':"xxx", ''kwargs':{'key1':value1, 'key2':'value2'}}, queue='louis-demo')
            # 'kwargs' inside the dict should be the arguments that you want to delive to 'code'
            # kwargs outside the dict must be written when call function apply_async
            # id should be the script uid in redis key
            # queue: where you want to send this task to

    """

    EXECUTE_CODE = '''
try:
    _celery_task = main
    _celery_task()
except:
    raise Exception
'''

    def __init__(self):
        super(_AsyncTask, self).__init__()
        self.id = None
        self.kwargs = None
        self.code = None

    def get_script_code(self, task_id):

        data = {'task_id': task_id}
        request = requests.get(url='https://ned83.cn.ibm.com/api/v2/current/celery_task', params=data, verify=False)
        print(request.url)
        result = json.loads(request.content)
        result = result['data']
        key = list(result.keys())[0]
        result = result[key]
        code = result['value']
        self.code = code

    def joint_code_kwargs(self, kwargs):

        code1 = self.EXECUTE_CODE[:self.EXECUTE_CODE.index('(')+1]
        code2 = self.EXECUTE_CODE[self.EXECUTE_CODE.index(')'):]
        codeM = ''
        for key in kwargs.keys():
            if type(kwargs[key]) == str:
                codeM = codeM + key + "=" + "'{}'".format(kwargs[key]) + ","
            else:
                codeM = codeM + key + "=" + str(kwargs[key]) + ","

        self.EXECUTE_CODE = code1 + codeM + code2
        self.code = """{}{}""".format(self.code, self.EXECUTE_CODE)

    def code_task(self):

        print(self.code)
        exec(self.code)

    def run(self, task_id, kwargs):

        self.get_script_code(task_id)

        self.joint_code_kwargs(kwargs)

        return self.code_task()


@celery_app.task
def task_manager():

    # todo get all the valid groups
    # group: name, uuid, tasks[task1(params), task2(params), task3(params), task4(params)],
    #        start_time, end_time, interval, end_date
    groups = [
        {'name': 'webex_overview',
         # 'start_time':'',
         # 'end_time':'',
         # 'end_date': '2019-09-01',
         'interval': 300,
         'last_exec_time':'1565325126',
         'tasks': [
             {'task_id':'7d9e85ccb9a111e99d82f45c89a98579', 'kwargs':{},
              'queue':'CM@webex_spark', 'room': 'web_spark', 'worker':'', },

             {'task_id': '7d9e85ccb9a111e99d82f45c89a98579', 'kwargs': {},
              'queue':'CT@webex_spark', 'room': 'web_spark', 'worker':''},
         ]

         },
        ]
    now = int(time.time())

    for group in groups:

        if now > group['last_exec_time'] + group['interval']:
            for task in group['tasks']:
                data = {}
                data['task_id'] = task['task_id']
                data['kwargs'] = task['kwargs']
                data['queue'] = task['queue']
                data['worker'] = task['worker']
                data['name'] = group['name']
                request = requests.post(url='https://ned100.cn.ibm.com:4433/task/assgin', params=data, verify=False)


AsyncTask = _AsyncTask()
celery_app.register_task(AsyncTask)


# =================== timing tasks
celery_app.conf.beat_schedule = {
    # 'CM_webex_spark_task': {
    #     'task': 'beacon.libs.celery._AsyncTask',
    #     'schedule': 300.0,
    #     'kwargs': {'task_id': '7d9e85ccb9a111e99d82f45c89a98579', 'kwargs': {}},
    #     'options': {'queue': "CM@webex_spark"}
    # },
    #
    # 'CT_webex_spark_task': {
    #     'task': 'beacon.libs.celery._AsyncTask',
    #     'schedule': 300.0,
    #     'kwargs': {'task_id': '7d9e85ccb9a111e99d82f45c89a98579', 'kwargs': {}},
    #     'options': {'queue': "CT@webex_spark"}
    # }
    'task_management': {
        'task': 'beacon.libs.celery.task_manager',
        'schedule': 60.0,
        'options': {'queue': "task_manager"}
    },
}


# ===================== signals
# @celeryd_after_setup.connect
# def celeryd_after_setup_test(sender, instance, conf, **kwargs):
#     print('=====setup worker')
#     queue_name = '{0}.dq'.format(sender)  # sender is the nodename of the worker
#     instance.app.amqp.queues.select_add(queue_name)
#     print(sender)
#     print(instance)
#     publisher('=====setup worker')
    # print(conf)


# @before_task_publish.connect
# def before_task_publish_test(**kwargs):
#     print('=====before_task_publish')
#     sender('worker:{} task_id:{}  status:{} timestamp:{} '.format(
#         kwargs['routing_key'],  kwargs['headers']['id'], 'publishing', time.time(),
#     ))
#
#
# @after_task_publish.connect
# def after_task_publish_test(**kwargs):
#     print('=====after_task_publish')
#     sender('worker:{} task_id:{}  status:{} timestamp:{} '.format(
#         kwargs['routing_key'],  kwargs['headers']['id'], 'published', time.time(),
#     ))
# @task_prerun.connect
# def task_prerun_test(**kwargs):
#     print('=====task_prerun')
#     sender('task_id:{}  status:{} timestamp:{} '.format(
#         kwargs['task_id'], 'executing', time.time(),
#     ))
#
#
# @task_postrun.connect
# def task_postrun_test(**kwargs):
#     print('=====task_postrun')
#     sender('task_id:{}  status:{} timestamp:{} state:{} return:{}'.format(
#         kwargs['task_id'], 'done', time.time(), kwargs['state'], kwargs['retval']
#     ))


# @eventlet_pool_apply.connect
# def eventlet_pool_apply_test(target=None, *args, **kwargs):
#     print('=====eventlet_pool_apply')
#     print(time.time())
#     print(kwargs['args'])
#     print(kwargs['kwargs'])


# @user_preload_options.connect
# def user_preload_options_test(app=None, options=None, **kwargs):
#     print('=====user_preload_option')
#     print(time.time())
#     print(app)
#     print(options)
#     print(kwargs)

# signals reference doc: http://docs.celeryproject.org/en/latest/userguide/signals.html
# ===================== signals

# Function about task, DO NOT DELETE.  Louis
# @celery_app.task
# def code_task(code=None):
#
#     code = code if code else CODE_EXAMPLE
#     code = """{}{}""".format(code, EXECUTE_CODE)
#     print(code)
#     exec(code)
#     return {"result": TASK_RESULT}
#
#
# @celery_app.task
# def script_task(file_name=None):
#
#     file_name = file_name if file_name else 'hello.py'
#     command = command_joint(file_name)
#     print(command)
#     try:
#         import os
#         result = os.system(command)
#         return result
#
#     except Exception as e:
#         raise e

# class CustomTask(Task):
#
#     def run(self):
#         return 'hello'
#
#
# task = CustomTask()
# celery_app.register_task(task)
