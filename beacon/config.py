

# celery configuration
accept_content = ['json']

task_serializer = 'json'

# broker_url = 'amqp://guest:guest@127.0.0.1:5672/'
#
# result_backend = 'redis://127.0.0.1:6379/1'
rabbitmq_host = '9.111.147.121'

broker_url = 'amqp://nedgp:admin123@9.111.147.121:5672/'
# broker_url = 'redis://9.111.147.121:6379/'
result_backend = 'redis://9.111.147.121:6379/1'