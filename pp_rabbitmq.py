'''
pp_rabbitmq.py

RabbitMQ and connection string
'''

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='pp', type='direct')
channel.queue_declare(queue='processing', durable=True)
channel.queue_declare(queue='printing', durable=True)
channel.queue_declare(queue='uploading', durable=True)
channel.queue_bind(exchange='pp', queue='processing', routing_key='processing')
channel.queue_bind(exchange='pp', queue='printing', routing_key='printing')
channel.queue_bind(exchange='pp', queue='uploading', routing_key='uploading')

def send(queue, message):
	channel.basic_publish(
		exchange='pp',
		routing_key=queue,
		body=message,
		#properties=pika.BasicProperties(delivery_mode=2)
	)
