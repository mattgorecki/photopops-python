#!/bin/bash
export DISPLAY=:0

/opt/google/chrome/google-chrome --kiosk --disable-restore-background-contents --disable-connect-backup-jobs --media-cache-size=1 --disk-cache-size=1 http://127.0.0.1:8000/tv
