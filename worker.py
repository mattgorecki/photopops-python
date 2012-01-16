'''
worker.py

RabbitMQ worker process
Run functions in the pp_actions module. 
build_1_up, build_4_up, greenscreen, send to printer, etc.
'''

import pp_actions
import pp_rabbitmq
import time

def callback(ch, method, properties, body):
	print " [x] Received %r" % (body)
	ch.basic_ack(delivery_tag = method.delivery_tag)

print ' [*] Waiting for messages. To exit press CTRL+C'
pp_rabbitmq.channel.basic_qos(prefetch_count=1)
pp_rabbitmq.channel.basic_consume(callback, queue='photopops')
pp_rabbitmq.channel.start_consuming()
