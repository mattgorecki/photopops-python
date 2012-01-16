'''
pp_connections.py

RabbitMQ and Socket.IO connection strings
'''

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='photopops', durable=True)

def send(message):
	channel.basic_publish(
		exchange='',
		routing_key='photopops',
		body=message,
		properties=pika.BasicProperties(delivery_mode=2)
	)
