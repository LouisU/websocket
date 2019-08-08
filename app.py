# encoding: utf-8

from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect, Namespace
import json
from flask_cors import CORS
from beacon.libs.celery import AsyncTask
import time
import uuid
from redis import Redis
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 新加入的代码-开始
thread = None
thread_lock = Lock()
op_redis = Redis(host="9.111.147.121", db=3, port=6379)

app = Flask(__name__)

# args about socket io
app.config['SECRET_KEY'] = 'secret!'

CORS(app)
socketio = SocketIO(app)


# def background_thread():
#     """Example of how to send server generated events to clients."""
#     # count = 0
#     # while True:
#     #     socketio.sleep(20)
#     #     count += 1
#     #     socketio.emit('my_response',
#     #                   {'data': 'Server generated event', 'count': count},
#     #                   namespace='/test')
#     pass

@app.route('/demo4/code/pull', methods=['post'])
def code_pull():

    data = json.loads(request.data)
    uid = data['id']
    code = op_redis.get(uid)
    print(code)
    return code


@app.route('/demo4/code/push', methods=['post'])
def code_push():
    data = json.loads(request.data)
    file = data['file']
    code = read_code(file)
    uid = uuid.uuid1().hex
    op_redis.set(uid, code)
    return jsonify({'task_id':uid})


@app.route('/demo4/task', methods=['post'])
def celery_task():
    data = json.loads(request.data)
    agent = data['agent']
    task = data['task']
    task_uid = data['task_uid']
    kwargs = data['kwargs']
    if task == 'sniff' or task == 'webex':
        beacon_id = agent
    elif task == 'ping' or task == 'browser':
        beacon_id = uuid.uuid1().hex
    else:
        return jsonify({'error': 'This is no task named {}'.format(task)})

    AsyncTask.apply_async(kwargs={'id': task_uid, 'kwargs': kwargs}, queue=agent)

    return jsonify({'beacon_id': beacon_id})


@app.route('/demo4/webex', methods=['get'])
def webex_tasks():

    agent = request.args.get('agent')
    # task_type = request.args.get('task_type')

    beacon_id = agent

    AsyncTask.apply_async(
        kwargs={'id': '4d4e745cb1b511e9ad50f45c89a98579'},
        queue=agent
    )
    return jsonify({'beacon_id': beacon_id})


@app.route('/demo4/sniff', methods=['get'])
def data_sniff():
    agent = request.args.get('agent')
    task_type = request.args.get('task_type')

    beacon_id = agent
    AsyncTask.apply_async(
        kwargs={'id': 'a2b46576b1a811e9989af45c89a98579',
                'kwargs': {'args': {"task_type": task_type, "beacon_id":beacon_id}}
                },
        queue=agent
    )
    return jsonify({'beacon_id': beacon_id})


@app.route('/demo4/ping', methods=['get'])
def ping_tasks():

    agent = request.args.get('agent')
    ping_parameter_list = [
        {'target': 'www.baidu.com'},
        {'target': 'www.ibm.com'},
        {'target': 'w3.ibm.com'},
        {'target': 'ned100.cn.ibm.com'},
        {'target': '9.0.149.140'}
    ]
    beacon_id = uuid.uuid1().hex

    code = read_code('ping')
    for target in ping_parameter_list:
        # task_id_u = uuid.uuid1()
        # task_id = task_id_u.hex
        # print(task_id)
        # task = AsyncTask.apply_async(
        #     kwargs={
        #         'file_name': 'ping',
        #         'kwargs': ['"{}"'.format(str({"target": target['target'], "task_id":beacon_id}))]
        #     }, queue=agent)
        task = AsyncTask.apply_async(
            kwargs={
                'id': 'f9febe28af7111e9bfccf45c89a98579',
                'kwargs': {"params":{"target": target['target'], "task_id": beacon_id}}
            }, queue=agent)
        # print(task.id)

    return jsonify({'beacon_id': beacon_id})


@app.route('/demo4/browser', methods=['get'])
def browser_tasks():

    agent = request.args.get('agent')

    browser_parameter_list = [
        {'target': 'https://www.baidu.com'},
        {'target': 'https://www.ibm.com'},
        {'target': 'https://w3.ibm.com'},
        {'target': 'https://ned100.cn.ibm.com:19002'},
        {'target': 'https://ecloud.10086.cn/about/aboutus'}
    ]

    beacon_id = uuid.uuid1().hex
    for target in browser_parameter_list:
        # task_id_u = uuid.uuid1()
        # task_id = task_id_u.hex
        task = AsyncTask.apply_async(
            kwargs={
                'id': '883650bcb1a611e99317f45c89a98579',
                'kwargs': {'params': {"target": target['target'], "task_id":beacon_id}}
            }, queue=agent)

        # task_id_list.append(task.id)

    return jsonify({'beacon_id': beacon_id})


def read_code(file_name):
    try:
        file = open('beacon/libs/tasks/{}.txt'.format(file_name), mode='rb')
        code = file.read()
        code = str(code, encoding='utf-8')

        return code
    except FileNotFoundError as e:
        raise e


@app.route('/demo4/jabber', methods=['get'])
def jabber_task():

    agent = request.args.get("agent")
    number = "*321"
    try:
        time = int(request.args.get("time"))
    except Exception as e:
        time = 180
    # todo change the py code to string code
    # file = open('beacon/libs/tasks/jabber.txt', mode='rb')
    # code = file.read()
    # code = str(code, encoding='utf-8')
    code = read_code('jabber')

    beacon_id = agent
    task = AsyncTask.apply_async(
        kwargs={
            'id': '76966a36af7b11e9b58ff45c89a98579',
            'kwargs': {'number': number, 'time_s':time}
        }, queue=agent)
    # beacon_id = agent
    # task = AsyncTask.apply_async(
    #     kwargs={
    #         'file_name': 'jabber',
    #         'kwargs': [number, time]
    #     }, queue=agent)


    return jsonify({'beacon_id': beacon_id})

@app.route('/webex', methods=['post'])
def webex_data():

    if not request.data:
        return ()
    data = json.loads(request.data)
    data['namespace'] = '/demo4'
    try:
        room = data['room']
        send_room_message2(data)
        return jsonify(data['webex'])
    except Exception as e:
        return jsonify({'error': 'Room does not exist.'})


@app.route('/async_test', methods=['post'])
def async_test():
    code = '''
def add_func():
    return 1+1
func = add_func
'''
    data = json.loads(request.data)

    tasks = int(data['tasks'])
    try:
        print(time.ctime())
        loop = tasks
        for i in range(loop):

            task = AsyncTask.apply_async(kwargs={'code': code}, queue='louis')
            if i == 0:
                print("First taskID: celery-task-meta-{}".format(task.task_id))
            elif i == loop - 1:
                print("Last taskID: celery-task-meta-{}".format(task.task_id))
        print(time.ctime())
        return jsonify({'is_send': True})

    except Exception as e:

        return jsonify({'is_send': False, 'error': str(e)})


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/demo4')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/demo4')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/demo4')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    # emit('my_response',
    #      {'data': 'In rooms: ' + ', '.join(rooms()),
    #       'count': session['receive_count']})


@socketio.on('leave', namespace='/demo4')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/demo4')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/demo4')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('my_room_event', namespace='/demo4')
def send_room_message2(message):
    # session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['webex']},
         room=message['room'], namespace=message['namespace'])


@socketio.on('disconnect_request', namespace='/demo4')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.on('my_ping', namespace='/demo4')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/demo4')
def test_connect():
    # emit('my_response', {'data': 'Connected', 'count': 0})
    pass

@socketio.on('disconnect', namespace='/demo4')
def test_disconnect():
    # print('Client disconnected', request.sid)
    pass

@socketio.on('client_event')
def client_msg(msg):
    emit('server_response', {'data': msg['data']})


@socketio.on('connect_event')
def connected_msg(msg):
    emit('server_response', {'data': msg['data']})


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
