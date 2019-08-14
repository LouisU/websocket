
def main(target, group_id):
    import requests
    import json
    from redis import Redis

    def post_data_to_socketroom(room, data):
        json_data = {
            "webex": data,
            "room": room
        }
        print("received:{}".format(json_data))
        requests.post('https://ned100.cn.ibm.com:4433/webex', data=json.dumps(json_data), verify=False)

    request = requests.get(target, verify=False)
    print(request.url, request.status_code, request.content)
    result = {'result': (request.url, request.status_code, str(request.content))}

    # store the result to redis
    key = '/group/task/result/{}/'.format(
        group_id,
    )
    value = json.dumps(result)
    op_redis = Redis(host="9.111.147.121", db=5, port=6379)
    op_redis.set(key, value)

    # send the result to Websocket
    post_data_to_socketroom(group_id, value)


