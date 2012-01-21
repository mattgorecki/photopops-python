'''
PhotoPops.py
'''

import Image
import ImageEnhance
import json
import os
import pika
import re
import serial
import shutil
from lib.socketio import SocketIO
import subprocess
import sys
import time

import pp_rabbitmq
from etc import settings
from pp_helpers import loadconfig,saveconfig

# Load config values from etc/photopops.cfg
def loadconfig():
	global cfg, EVENTNAME, TMPDIR, EV_DIR, EV_ORIG_DIR, EV_PROC_DIR, USB_DIR, WATERMARK

	cfgfile = open('/opt/photopops/etc/photopops.cfg')
	cfg = json.load(cfgfile)
	cfgfile.close()

	EVENTNAME = cfg['shortname']
	TMPDIR = "/tmp/photopops"
	EV_DIR = "/opt/photopops/events/%s" % EVENTNAME
	EV_ORIG_DIR = "/opt/photopops/events/%s/orig" % EVENTNAME
	EV_PROC_DIR = "/opt/photopops/events/%s/proc" % EVENTNAME
	EV_MARKED_DIR = "/opt/photopops/events/%s/marked" % EVENTNAME
	EV_FINAL_DIR = "/opt/photopops/events/%s/final" % EVENTNAME
	USB_DIR = "/media/photopops"

	# Make sure directories exist
	if not os.path.isdir(TMPDIR):
		os.mkdir(TMPDIR)
	if not os.path.isdir(EV_DIR):
		os.mkdir(EV_DIR)
	if not os.path.isdir(EV_ORIG_DIR):
		os.mkdir(EV_ORIG_DIR)
	if not os.path.isdir(EV_MARKED_DIR):
		os.mkdir(EV_MARKED_DIR)
	if not os.path.isdir(EV_FINAL_DIR):
		os.mkdir(EV_FINAL_DIR)
	if not os.path.isdir(EV_PROC_DIR):
		os.mkdir(EV_PROC_DIR)

loadconfig()

# Connect to Arduino
s = serial.Serial('/dev/ttyACM0');

# Node.js connection
sio = SocketIO()
sio.send("log_event", "PhotoPops.py started")
lastheartbeat = time.time()

# For storing the filenames of a multiple-shot set.
photo_list = list()

def download_photo():
	''' Download photo from camera with gphoto2. Delete photo from camera immediately.  Return filename. '''
	print "Downloading photo...",

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
	
	# Return filename of photo
	return fn

def rotate_resize_for_tv(fn):
	''' Initial photo process.  
	Only save a single file that's 1080x1920 to display on TV.
	Greenscreen processing will happen later.
	'''

	# Move original photo to event directory
	shutil.move("%s/%s" % (TMPDIR, fn), "%s/%s" % (EV_ORIG_DIR, fn))
	orig_fullpath = "%s/%s" % (EV_ORIG_DIR, fn)
	proc_fullpath = "%s/%s" % (EV_PROC_DIR, fn)

	# Rotate photo
	im = Image.open("%s/%s" % (EV_ORIG_DIR, fn))
	im = im.rotate(-90, expand=True)
	im.save("%s/%s" % (EV_ORIG_DIR, fn), "JPEG", quality=90)

	# Generate 1080x1920 for TV display
	thumb_tv = im.copy()
	thumb_tv.thumbnail((1080,1920), Image.NEAREST)
	thumb_tv = thumb_tv.rotate(90, expand=True)
	thumb_tv.save("/opt/photopops/web/img/thumbs/1920-%s" % (fn), 'JPEG', quality=90)

	sio.send("log_event", "Photo processed")
	sio.send("tv_photo_taken", "1920-%s" % (fn))

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
				# Load JSON from etc/photopops.cfg
				loadconfig()

				# Notify TV display that button was pressed, via node.js
				# This will start the countdown animation and wait for a few seconds
				# before snapping the photo.
				sio.send("button_pressed", "")
				time.sleep(settings.T_COUNTDOWN)

				# Ready to take picture.  Send a "B" to trigger shutter
				s.write("B")

			if serialvalue == "C":
				# Photo was taken
				print "Photo captured"

				# Wait for camera to finish writing photo before downloading.
				time.sleep(settings.T_CAPTURE_DUR)

				fn = download_photo()
				if not fn:
					# Camera didn't capture or errored out.  Send 'D' to reset Arduino and go to next iteration.
					print "Camera error.  No file exists by %s" % fn
					s.write("D")
					continue

				# Initial resize of photo.  Rotate photo 90 degrees.
				# This will display on the TV.
				rotate_resize_for_tv(fn)

				# Green screen process
				if cfg['greenscreen'] == "True":
					#pp_rabbitmq.send('{"action":"greenscreen","filename":"%s"}' % fn)
					shutil.copy("%s/%s" % (EV_ORIG_DIR, fn), "%s/%s" % (EV_PROC_DIR, fn))
				else:
					# Copy original to processed so we have something to work with later.
					shutil.copy("%s/%s" % (EV_ORIG_DIR, fn), "%s/%s" % (EV_PROC_DIR, fn))

				# Copy original photo to USB stick
				if cfg['send_to_usbstick'] == "True":
					pp_rabbitmq.send('{"action":"send_to_usb","filename":"%s"}' % (fn))

				# Upload to Facebook
				if cfg['upload_to_photopops_fb'] == "True":
					pp_rabbitmq.send('{"action":"fb_upload","filename":"%s"}' % (fn))

				# Photo complete. Set Arduino to ready
				print "Loop for photo %s complete." % fn
				photo_list.append(fn)

				# Keep photo up on screen for a few seconds
				# and ignore any button presses
				time.sleep(settings.T_TVPREVIEW)

				# Only write D to re-enable the button if the whole cycle is complete. Otherwise, send B to do it again.
				if len(photo_list) == cfg['number_up']:
					print "Captured %s photos" % len(photo_list)
					print photo_list

					# QUEUE EVENT: send to printer
					if cfg['send_to_printer'] == "True":
						print "Printing...",
						#pp_rabbitmq.send("printing", '{"files":%s}' % json.dumps(photo_list))

						if cfg['number_up'] == 1:
							print "number up is 1"
							pp_rabbitmq.send('{"action":"build_1_up", "files":%s, "send_to_printer":"%s"}' % (json.dumps(photo_list), cfg['send_to_printer']))
						sio.send("log_event", "Sending to printer")
						print "done."

					s.write("D")

					# Clear photo_list
					photo_list = list()
				else:
					# Still need more photos.  Run countdown again.

					# Notify TV display that button was pressed, via node.js
					sio.send("button_pressed", "")
					time.sleep(settings.T_COUNTDOWN)

					# Ready to take picture.  Send a "B" to trigger shutter
					s.write("B")
					print "sending B #%d" % len(photo_list)

	except KeyboardInterrupt:
		print "Closing PhotoPops."
		sio.send("log_event", "PhotoPops.py shutting down.")
		del sio
		sys.exit()
