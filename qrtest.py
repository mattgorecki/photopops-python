from lib.pyQR import *
import Image


qr = QRCode(4, QRErrorCorrectLevel.L)
#TODO: Generate album URL for QR Code if it doesn't exist
qr.addData("http://asdfij.com/asdiuasdfkjhqw34io5ubasdklfubgaljsbtfo3nsadf/asdf9n3215ui")
qr.make()
qr_im = qr.makeImage()
qr_im = qr_im.resize((175,175), Image.NEAREST)
qr_im.save("qrjpeg.jpg", "JPEG", quality=90)
