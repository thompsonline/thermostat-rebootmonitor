#!/usr/bin/env python

import signal
import logging
import logging.handlers
import ConfigParser

import os
import psutil 
import time 
import datetime
import sys 
from ISStreamer.Streamer import Streamer

# -- Get configuration information
dname = os.path.dirname(os.path.abspath(__file__))

# read values from the config file
config = ConfigParser.ConfigParser()
config.read(dname + "/config.txt")

# -- Setup Logging
logLevelConfig = config.get('logging', 'loglevel')
if logLevelConfig == 'info':
    LOG_LOGLEVEL = logging.INFO
elif logLevelConfig == 'warn':
    LOG_LOGLEVEL = logging.WARNING
elif logLevelConfig ==  'debug':
    LOG_LOGLEVEL = logging.DEBUG

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LOGLEVEL)
handler = logging.handlers.TimedRotatingFileHandler(config.get('logging','logfile'), 
                                                    when=config.get('logging','logrotation'), 
                                                    backupCount=int(config.get('logging','logcount')))
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MyLogger(object):
        def __init__(self, logger, level):
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

sys.stdout = MyLogger(logger, logging.INFO)
sys.stderr = MyLogger(logger, logging.ERROR)


def main(argv):
        logger.info('Reboot' + ((': ' + argv[1]) if len(argv) > 1 else ''))

	# Wait for ntpd to run for sync of the clock
	found_ntpd = False
	cnt = 0
	while found_ntpd == False and cnt < 60:
		for proc in psutil.process_iter():
			if proc.name() == "ntpd":
				found_ntpd = True

		if found_ntpd == False:
			logger.debug("ntpd not started")
			time.sleep(1)
			cnt += 1

	logger.debug("ntpd started. Waiting...")
	time.sleep(60*int(config.get('main','delay')))

	streamer = Streamer(bucket_name=config.get('initialState','BucketName'), 
                            bucket_key=config.get('initialState','BucketKey'), 
                            access_key=config.get('initialState','AccessKey'))
	streamer.log(config.get('initialState','ProcessName'), "Rebooted" + ((' :' + argv[1]) if len(argv) > 1 else ''))
	streamer.flush() 
	
	
if __name__ == "__main__":
	main(sys.argv)	
