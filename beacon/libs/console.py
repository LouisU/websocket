
import pika


class WorkerInfo:

    def __init__(self, host='9.111.147.121', queue='worker_info'):
        self.__user_pwd = pika.PlainCredentials('nedgp', 'admin123')
        self.__queue = queue
        self.__rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=self.__user_pwd)
        )
        self.__channel = self.__rabbitmq_connection.channel()
        self.__channel.queue_declare(queue=queue, durable=True)

    def publish(self, message):
        self.__channel.basic_publish(
            exchange='',
            routing_key=self.__queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        print(" [x] Sent '{}'".format(message))
        self.__rabbitmq_connection.close()

    def _callback(self, ch, method, properties, body):
        print("[x] {} ".format(body))

    def receive(self):
        self.__channel.basic_consume(
            queue=self.__queue, on_message_callback=self._callback, auto_ack=True
        )
        print(' [*] Waiting for logs. To exit press CTRL+C')
        self.__channel.start_consuming()


if __name__ == "__main__":

    consumer_console = WorkerInfo()
    consumer_console.receive()
