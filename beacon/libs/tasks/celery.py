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


celery_app = Celery('celery_app')
celery_app.config_from_object('beacon.config')


# send worker logs into rabbitmq
def sender(message):
    publisher = WorkerInfo()
    publisher.publish(message)


class _AsyncTask(Task):
    """
    usage1: AsyncTask.apply_async(kwargs={'code':"def ...", ''kwargs':{'a':1, 'b':{'a':1, 'b':2}, 'c':(1,2,3), 'd':[1,2,3], 'e': 'start'}}, queue='louis-demo')
            # code should be the string of function that you want to run. Note that, the last line of the code must be "func = youfunctionname "
            # 'kwargs' inside the dict should be the arguments that you need to add to 'code'
            # kwargs outside the dict must be written when call function apply_async
            # queue: where you want to send this task to

    usage2: AsyncTask.apply_async(kwargs={'file_name':'hello'}, queue='louis-demo')
            # hello.py should under the directory "beacon/libs/tasks/", location: "beacon/libs/tasks/hello.py"
            # queue: where you want to send this task to

    """
    # The variable only for test. Louis
    CODE_EXAMPLE = '''
def main(counter):
    import time
    sum = 0
    for i in range(counter):
        time.sleep(1)
        sum += i
    return sum
_celery_task = main
'''

    EXECUTE_CODE = '''
try:
    result = _celery_task()
    self.pass_result(result)
except:
    raise Exception
'''
    CODE_RESULT = None

    def __init__(self):
        super(_AsyncTask, self).__init__()
        self.file_name = None
        self.code = None
        self.__task_type = None

    def on_success(self, retval, task_id, args, kwargs):
        # print('task id:{} done. result:{}.'.format(task_id, retval))
        return super(_AsyncTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # print('task_id:{} failed. reason:{}.'.format(task_id, exc))
        return super(_AsyncTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def pass_result(self, result):
        self.CODE_RESULT = result

    def code_or_script(self, code, file_name, kwargs):
        # print('code:{}'.format(code))
        # print('file_name:{}'.format(file_name))
        if file_name is None and code is None \
                or file_name is not None and code is not None:
            raise TypeError(
                "{} has two arguments. one is required,  "
                "other one must be None or ignored.".format(self.__class__.__name__)
            )

        if file_name is not None and re.search(r'\.py$', file_name) is None:
            self.file_name = file_name + '.py'

            self.__task_type = "script"
            self.__args = kwargs

        if code is not None:
            if code == 'test':
                self.__task_type = "code"
                self.code = self.CODE_EXAMPLE
                self.__kwargs = kwargs
            else:

                if re.search(r'.*_celery_task\s*=.*', code) is None:
                    raise ValueError(
                        'Please make sure your function was assigned to _celery_task '
                        'at the last line of code string. e.g. _celery_task = yourfunction  '
                    )
                else:
                    self.__task_type = "code"
                    self.code = code
                    self.__kwargs = kwargs

    def get_args_or_kwargs(self):

        if self.__task_type == 'code':
            # code = """{}{}""".format(self.code, self.EXECUTE_CODE)
            # brackets_index = re.search('.*(.*):', self.EXECUTE_CODE).span()[1]
            # if brackets_index > self.EXECUTE_CODE.index('(') \
            #         and brackets_index > self.EXECUTE_CODE.index(')'):
            code1 = self.EXECUTE_CODE[:self.EXECUTE_CODE.index('(')+1]
            code2 = self.EXECUTE_CODE[self.EXECUTE_CODE.index(')'):]
            codeM = ''
            for key in self.__kwargs.keys():
                if type(self.__kwargs[key]) == str:
                    codeM = codeM + key + "=" + "'{}'".format(self.__kwargs[key]) + ","
                else:
                    codeM = codeM + key + "=" + str(self.__kwargs[key]) + ","

            self.EXECUTE_CODE = code1 + codeM + code2
            self.code = """{}{}""".format(self.code, self.EXECUTE_CODE)

        if self.__task_type == 'script':
            args_str = ''
            if type(self.__args) == list:
                # print('args dic: {}'.format(self.__args))

                for arg in self.__args:
                    args_str = args_str + ' {}'.format(arg)

            self.args_str = args_str
            # print("agrs str joint:{}".format(self.args_str))

    def _command_joint(self):
        directory = path.dirname(__file__)
        file_directory = directory + '/tasks/' + self.file_name
        # print(self.args_str)
        command = 'python ' + file_directory + self.args_str
        # print(command)
        return command

    def code_task(self):
        # code = """{}{}""".format(self.code, self.EXECUTE_CODE)
        print(self.code)
        exec(self.code)
        return {"result": self.CODE_RESULT, 'time': time.ctime()}

    def script_task(self):
        command = self._command_joint()
        # print(command)
        try:
            import os
            result = os.system(command)
            return result

        except Exception as e:
            raise e

    def run(self, code=None, kwargs=None, file_name=None):

        if file_name == 'selenium_webex':

            try:
                import os
                command = 'xvfb-run --server-args="-screen 0 1024x768x24" python /webex_demo/selenium_webex.py'
                result = os.system(command)
                return result

            except Exception as e:
                raise e

        self.code_or_script(code, file_name, kwargs)

        self.get_args_or_kwargs()
        # print('task type:{}'.format(self.__task_type))
        if self.__task_type == 'script':
            return self.script_task()
        else:
            return self.code_task()


AsyncTask = _AsyncTask()
celery_app.register_task(AsyncTask)

# ===================== beat task
# celery_app.conf.beat_schedule = {
#     'script-task-every-60-seconds': {
#         'task': 'beacon.libs.celery._AsyncTask',
#         'schedule': 60.0,
#         'kwargs': {'file_name': 'hello', 'code': None},
#         'options': {'queue': "louis"}
#     },
#
#     'code-task-every-30-seconds': {
#         'task': 'beacon.libs.celery._AsyncTask',
#         'schedule': 30.0,
#         'kwargs': {'code': AsyncTask.CODE_EXAMPLE, 'kwargs': {'counter': 9}},
#         'options': {'queue': "louis"}
#     }
#
# }


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
