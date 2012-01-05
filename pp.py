'''
PhotoPops.py
'''

import beanstalkc
import facebook
import Image
import ImageEnhance
import json
import os
import re
import serial
import shutil
from socketio import SocketIO
import subprocess
import sys
import time

# Initialization settings
photo_list = list()

# Connect to beanstalk
beanstalk = beanstalkc.Connection(host='localhost', port=11300)
beanstalk.use('pp')

# Connect to database via web2py DAL
sys.path.append("/opt/web2py")
from gluon import DAL
db = DAL('sqlite://storage.sqlite', folder='/opt/web2py/applications/photopops/databases', auto_import=True)

# Connect to Arduino
s = serial.Serial('/dev/ttyACM0');

# Node.js connection
sio = SocketIO()
sio.send("log_event", "PhotoPops.py started")
lastheartbeat = time.time()

# Facebook Token setup
FB_TOKEN='AAABs3ZCR0wIEBAJbl43Ebky3Y5iq0YPKGTpAEmk0yZBJTL4BfNLExBmSvZCEkYtavTlPKfZAYDZCP0GUC1ouLscGt999FRZBxILhBsOkemAgZDZD' # PhotoPops app token
FB_PAGE_ID='216861271706571' # PhotoPops Facebook Page
graph = facebook.GraphAPI(FB_TOKEN)

def download_photo():
	''' Download photo from camera with gphoto2. Delete photo from camera immediately.  Return filename. '''
	print "Downloading photo...",
	starttime = time.time()
	global TMPDIR

	# Save file to tmp directory
	os.chdir(TMPDIR)

	# Photo already on camera, download it
	p = subprocess.Popen(['/usr/bin/gphoto2', '-R', '--get-file', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	res = p.communicate()

	# Check for errors before continuing
	m = re.search("(Error)",res[1])
	if m is not None:
		sio.send("log_event", "Camera errored out")
		return False

	# Pull photo filename from gphoto2 output
	m = re.search("(\w+_\d+.JPG)", res[0])
	if not m.group(0):
		sio.send("log_event", "Camera capture output invalid")
		return False
	else:
		fn = m.group(0)

	# Delete photo from camera
	p = subprocess.Popen(['/usr/bin/gphoto2', '-R', '--delete-file', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	sio.send("log_event", "Photo %s captured" % fn)
	print "done."
	
	elapsed = time.time() - starttime
	print "download: %f elapsed" % elapsed

	return fn

def process_photo(fn, eventname, watermark=False):
	''' Process photo.  Add Photopops watermark. '''
	starttime = time.time()
	global EV_ORIG_DIR
	global EV_PROC_DIR

	# Open photo and watermark
	im = Image.open("%s/%s" % (EV_ORIG_DIR, fn))

	#print "Open photo took %f" % (time.time() - starttime)
	#starttime = time.time()

	if watermark:
		mark = Image.open(WATERMARK)

		if im.mode != 'RGBA':
			print "Converting %s/%s" % (EV_ORIG_DIR, fn)
			im = im.convert('RGBA')
		if mark.mode != 'RGBA':
			print "Converting %s/%s" % (EV_ORIG_DIR, fn)
			mark = mark.convert('RGBA')

		# Set opacity on watermark 
		alpha = mark.split()[3]
		alpha = ImageEnhance.Brightness(alpha).enhance(0.3)
		mark.putalpha(alpha)

		# Create a new transparent layer the size of the original image
		layer = Image.new('RGBA', im.size, (0,0,0,0))
		layer.paste(mark, (im.size[0]-mark.size[0]-50,im.size[1]-mark.size[1]-50))

		# Add watermark layer to original image and save in processed directory
		proc = Image.composite(layer, im, layer)
		proc.save("%s/%s" % (EV_PROC_DIR, fn), 'JPEG', quality=90)

		#print "Add watermark %f" % (time.time() - starttime)
		#starttime = time.time()
	else:
		# Save original image to Processed directory.
		# TODO: Shouldn't be necessary, but just to make sure there is something in processed
		# TODO: Move watermark to it's own function
		im.save("%s/%s" % (EV_PROC_DIR, fn), 'JPEG', quality=90)

	# Generate thumbnail for admin page
	# Generate 1920x1080 for TV display
	#thumb_admin = proc.copy()
	#thumb_tv = proc.copy()
	thumb_admin = im.copy()
	thumb_tv = im.copy()

	#print "Copy photo twice took %f" % (time.time() - starttime)
	#starttime = time.time()

	thumb_admin.thumbnail((425,283), Image.NEAREST)
	thumb_admin.save("%s/425-%s" % (EV_PROC_DIR, fn), 'JPEG', quality=90)

	#print "Save thumbnail took %f" % (time.time() - starttime)
	#starttime = time.time()

	thumb_tv.thumbnail((1620,1080), Image.NEAREST)
	thumb_tv.save("%s/1620-%s" % (EV_PROC_DIR, fn), 'JPEG', quality=90)

	#print "Save TV thumbnail took %f" % (time.time() - starttime)
	#starttime = time.time()

	sio.send("log_event", "Photo processed")
	sio.send("photo_taken", "/photopops/static/opt/%s/processed/425-%s" % (eventname, fn))
	sio.send("tv_photo_taken", "/photopops/static/opt/%s/processed/1620-%s" % (eventname, fn))

	#print "Send node event took %f" % (time.time() - starttime)
	print "Total photo took %f" % (time.time() - starttime)
	starttime = time.time()

while True:
	try:
		# Send heartbeat to socket.io every 15 seconds if there is no data in the Serial queue.
		if s.inWaiting() == 0:
			if time.time() - lastheartbeat >= 15:
				print "Sending heartbeat."
				sio.heartbeat()
				lastheartbeat = time.time()
			time.sleep(0.1)
		else:
			serialvalue = s.read()

			if serialvalue == "A":
				# Button pressed
				print "That was Easy."
				sio.send("log_event", "Easy Button pressed.")

				# Load event settings on every new button press iteration, so any changes will take effect.
				event = db(db.event).select(orderby=~db.event.id).first()

				# Load configuration settings
				EVENTNAME = event.shortname
				TMPDIR = "/tmp/photopops"
				EV_DIR = "/opt/photopops/%s" % EVENTNAME
				EV_ORIG_DIR = "/opt/photopops/%s/original" % EVENTNAME
				EV_PROC_DIR = "/opt/photopops/%s/processed" % EVENTNAME
				USB_DIR = "/media/photopops"
				WATERMARK = "/opt/photopops/assets/logo-angled-600x250.png"

				# Make sure directories exist
				if not os.path.isdir(TMPDIR):
					os.mkdir(TMPDIR)
				if not os.path.isdir(EV_DIR):
					os.mkdir(EV_DIR)
				if not os.path.isdir(EV_ORIG_DIR):
					os.mkdir(EV_ORIG_DIR)
				if not os.path.isdir(EV_PROC_DIR):
					os.mkdir(EV_PROC_DIR)

				# TODO: Adjust delays in Arduino
				# Notify TV display that button was pressed, via node.js
				sio.send("button_pressed", "")
				time.sleep(3.5)

				# Ready to take picture.  Send a "B" to trigger shutter
				s.write("B")

			if serialvalue == "C":
				# Photo was taken
				print "Photo captured"

				# Wait for camera to finish writing photo before downloading.
				time.sleep(2)

				fn = download_photo()
				if not fn:
					# Camera didn't capture or errored out.  Send 'D' to reset Arduino and go to next iteration.
					print "Camera error"
					s.write("D")
					continue

				# Move original photo to event directory
				shutil.move("%s/%s" % (TMPDIR, fn), "%s/%s" % (EV_ORIG_DIR, fn))
				orig_fullpath = "%s/%s" % (EV_ORIG_DIR, fn)
				proc_fullpath = "%s/%s" % (EV_PROC_DIR, fn)

				# Rotate photo
				im = Image.open("%s/%s" % (EV_ORIG_DIR, fn))
				im = im.rotate(90, expand=True)
				im.save("%s/%s" % (EV_ORIG_DIR, fn), "JPEG", quality=90)

				# Process Photo.  Resize, add logo, contrast and curves
				process_photo(fn, EVENTNAME)

				# Copy original photo to USB stick
				if event.send_to_usbstick:
					print "Saving to USB stick...",
					if os.path.isdir(USB_DIR):
						shutil.copyfile("%s/%s" % (EV_ORIG_DIR, fn), "%s/%s" % (USB_DIR, fn))
					else:
						# TODO: Add error notification for missing USB stick
						pass

					sio.send("log_event", "Copied to USB Stick")
					print "done."

				# Upload to Facebook
				'''
				if event.upload_to_facebook:
					print "Uploading to Facebook...",
					beanstalk.put('{"cmd":"fb_upload","filename":"%s"}' % proc_fullpath)

					sio.send("log_event", "Uploaded to Facebook")
					print "done."
				'''

				# Photo complete. Set Arduino to ready
				print "Photo %s complete." % fn

				photo_list.append(fn)

				# Keep photo up on screen for a few seconds
				time.sleep(5)

				# Only write D to re-enable the button if the whole cycle is complete. Otherwise, send B to do it again.
				if len(photo_list) == event.number_up:
					print "Captured %s photos" % len(photo_list)
					print photo_list

					# TODO: Building should be specified here

					if event.send_to_printer:
						print "Printing...",
						beanstalk.put('{"cmd":"print","files":%s}' % json.dumps(photo_list))
						sio.send("log_event", "Sending to printer")
						print "done."

					# TODO: Build composite photo and send to printer
					s.write("D")
					# Clear photo_list
					photo_list = list()
				else:
					# Still need more photos.  Run countdown again.

					# Notify TV display that button was pressed, via node.js
					sio.send("button_pressed", "")
					time.sleep(3.5)

					# Ready to take picture.  Send a "B" to trigger shutter
					s.write("B")
					print "sending B #%d" % len(photo_list)

	except KeyboardInterrupt:
		print "Closing PhotoPops."
		sio.send("log_event", "PhotoPops.py shutting down.")
		del sio
		sys.exit()
