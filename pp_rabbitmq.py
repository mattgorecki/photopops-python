'''
pp_rabbitmq.py

RabbitMQ and connection string
'''

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='pp', type='direct')
channel.queue_declare(queue='photopopsqueue', durable=True)
channel.queue_bind(exchange='pp', queue='photopopsqueue', routing_key='photopopsqueue')

def send(message):
	channel.basic_publish(
		exchange='pp',
		routing_key="photopopsqueue",
		body=message,
		#properties=pika.BasicProperties(delivery_mode=2)
	)
