'''
worker-printing.py
RabbitMQ worker process

Printing queue is only for printing the final processed photo.
'''

#import pp_actions
import pp_rabbitmq
import time

QUEUE='printing'

def callback(ch, method, properties, body):
	print " [x] Received %r" % (body)
	ch.basic_ack(delivery_tag = method.delivery_tag)

print ' [*] Waiting for messages. To exit press CTRL+C'
pp_rabbitmq.channel.basic_qos(prefetch_count=1)
pp_rabbitmq.channel.basic_consume(callback, queue=QUEUE)
pp_rabbitmq.channel.start_consuming()
