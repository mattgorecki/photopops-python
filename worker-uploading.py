'''
worker-uploading.py
RabbitMQ worker process

Uploading queue is for sending to Facebook, website, Flickr, Google+, etc.
'''

from pp_helpers import loadconfig,saveconfig
import etc.settings
import pp_rabbitmq
import time
import facebook

QUEUE='uploading'

def fb_upload():
	cfg = loadconfig()
	print cfg

	graph = facebook.GraphAPI(settings.FB_APP_TOKEN)
	
	if len(cfg['photopops_fb_album_id']) == 0:
		print "no album"
		fb_res = graph.put_object(settings.FB_PHOTOPOPS_PAGE_ID, "albums", name=cfg['title'], message=cfg['title'])
		cfg['photopops_fb_album_id'] = fb_res['id']
	else:
		album_id = cfg['photopops_fb_album_id']

	print album_id
	fb_photo = open(fn, "rb")
	fb_res = graph.put_photo(fb_photo,album_id,fn)
	fb_photo.close()

	del album_id

def callback(ch, method, properties, body):
	print " [x] Received %r" % body
	fb_upload()
	ch.basic_ack(delivery_tag = method.delivery_tag)

print ' [*] Waiting for messages. To exit press CTRL+C'
pp_rabbitmq.channel.basic_qos(prefetch_count=1)
pp_rabbitmq.channel.basic_consume(callback, queue=QUEUE)
pp_rabbitmq.channel.start_consuming()
