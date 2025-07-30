# logger.py
# developer: @eggins

import time, sys, threading

lock = threading.Lock()


class logger:

	# initalise base variable structure
	def __init__(self):
		# setting an array of colours to be used
		self.colours = {
			"error" 		: "[91m",
			"success" 		: "[92m",
			"info" 			: "[96m",
			"debug" 		: "[95m",
			"yellow" 		: "[93m",
			"lightpurple" 		: "[94m",
			"lightgray" 		: "[97m",
			"clear"			: "[00m"
		}

	def log(self, message="", color="", file="", shown=True, showtime=True, nocolor=""):
		# define the current time when calling the logger as HOUR:MINUTE:SECOND
		currentTime = time.strftime("%H:%M:%S")

		# define which colour is being used
		try:
			colourString = self.colours[color]
		except:
			colourString = ""

		# construct time string
		if showtime:
			timestring = "[%s] " % currentTime
		else:
			timestring = ""

		# path together the message and the clear colour
		messageString = str(message) + self.colours['clear']
		noColourString = str(message)

		store = "[FLICKET] "
		# add : and paste the content afterward
		if nocolor:
			messageString += ": %s" % nocolor 
			noColourString += ": %s" % nocolor 
        
		finalString = timestring+colourString+store+str(messageString)+"\n"
		noColourFinalString = timestring+store+str(noColourString)+"\n"

		# print from the system to the terminal
		# this method helps stop overlap when threading
		with lock:
			sys.stdout.write(finalString)
			sys.stdout.flush()

		# print message to file if requested
		if file:
			with open(file, "a") as f:
				f.write(noColourFinalString)
        
