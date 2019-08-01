
# Version 4.0 celery new lower case settings
#

# set broker and backend
rabbitmq_host = '9.111.147.121'

broker_url = 'amqp://ned83.cn.ibm.com:5672/'

# result_backend = 'redis://9.111.147.121:6379/1'


# set common configurations
accept_content = ['json']

task_serializer = 'json'

result_serializer = 'json'

timezone = 'Asia/Shanghai'

# enable_utc = True


# set if ignore task result
task_ignore_result = True

# set task queues
# task_queues =

# set task routing
# task_routes =

# set default exchange and default exchange type
# task_default_exchange_type = "direct"
# task_default_exchange =



# For testing
# broker_url = 'amqp://guest:guest@127.0.0.1:5672/'
# result_backend = 'redis://127.0.0.1:6379/1'