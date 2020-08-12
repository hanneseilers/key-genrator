# ---- CONFIG ----
inputFile = "input.csv"
usedKeysFile = "keys.txt"
inputDir = "input"
outputDir = "output"
# ---- CONFIG END ----

import os
from os import path
import logging
import json

import string
import secrets
import numpy as np
from functools import partial


class Filesystem:

	def check(self, inputDir, outputDir, inputFile, keysFile):
		logging.info("Checking existing files ...")
		if not path.exists( inputDir ):
			os.mkdir( inputDir )
			logging.warning( "Input directory " + inputDir + " not found! Created it." )
		
		if not path.exists( inputDir + "/" + inputFile ):
			logging.critical( "Input file " + str(inputFile) + " not found!" )
			return False
			
		if not path.exists( inputDir + "/" + keysFile ):
			logging.warning( "Keys file " + str(keysFile) + " not found! A new one will be created." )
			
		if not path.exists( outputDir ):
			os.mkdir( outputDir )
			logging.warning( "Output directory " + outputDir + " not found! Created it." )
			
		logging.info("... passed")
		return True
		
	def readKeys(self, keysFile):
		logging.info("Reading keys file, " + keysFile +  " ...")
		keys = set()
		
		if path.exists(keysFile):
			try:
				f = open( keysFile, 'r' )
				for line in f:
					keys.add( str(line).strip() )
			except:
				logging.error("ERROR")
			
		logging.info("... found " + str(len(keys)) + " keys.")
		return keys
		
	def readUsers(self, inputFile):
		logging.info("Reading input file, "+ inputFile + " ...")
		users = {}
		n = 0

		try:
			f = open( inputFile , 'r' )
			for line in f:
				line = line.strip().split(',')
				if len(line) > 2:
					userid = int(line[0].strip("\""))
					user = { 'name': str(line[1]).strip("\""), 'prename': str(line[2]).strip("\"") }
					group = str(line[3]).replace("\n", "").replace("\t", "").strip("\"")
					if group not in users:
						users[group] = {}
					users[group][userid] = user
					n += 1
		except:
			logging.error("ERROR")
				
		logging.info("... found " + str(n) + " users in " + str(len(users)) + " groups.")
		return n, users
		
	def writeUsersJson(self, userdata, usersFile="users.json"):
		logging.info( "Writing json formatted user data to " + usersFile )
		f = open(usersFile, 'w')
		f.write( json.dumps(userdata).replace(" ", "") )
		f.close()
		
	def writeKeys(self, keys=set(), keysfile="keys.txt"):
		logging.info( "Writing keys to " + keysfile )
		f = open( keysfile, 'w')
		for key in keys:
			f.write( str(key) + "\n" )
		f.close()
		
	def clean(self, dirs=[]):
		logging.info("Cleanup data")
		for d in dirs:
			if path.exists(d):
				for dirpath, dirnames, filenames in os.walk(d):
					for f in filenames:
						if not str(f).startswith('.'):
							os.remove( d + f )

class Main:

	filesystem = None
	inputFile = ""
	useKeysFile = ""
	outputDir = ""
	inputDir = ""
	
	userdata = {}
	n_userdata = 0
	keys = set()

	def __init__(self, inputDir, outputDir, inputFile, usedKeysFile):
		self.filesystem = Filesystem()
		self.inputFile = inputFile
		self.usedKeysFile = usedKeysFile
		self.outputDir = outputDir
		self.inputDir = inputDir

	def start(self):
		self.filesystem.clean( [self.outputDir+"/"] )

		if self.filesystem.check( self.inputDir, self.outputDir, self.inputFile, self.usedKeysFile ):
			self.keys = self.filesystem.readKeys( self.inputDir + "/" + self.usedKeysFile )
			self.n_userdata, self.userdata = self.filesystem.readUsers( self.inputDir + "/" + self.inputFile )
			
			keys = self.keys.copy()
			keys.update( self.produceKeys( self.n_userdata ) )
			self.assignKeys( keys )
			self.filesystem.writeUsersJson( self.userdata, self.outputDir + "/users.json" )
			self.filesystem.writeKeys(keys, self.outputDir + "/keys.txt")
			self.formattedOutput()
			logging.info( "done." )
			
			# ask for cleanup
			while self.ask( "Do you downloaded output?", ['y', 'n'] ) != "y":
				print( "\n\n\t\t>>>> DOWNLOAD OUTPUT NOW <<<<\n\n\n" )
			self.filesystem.clean( [self.inputDir+"/", self.outputDir+"/"] )
				
				
	def produceKeys(self, amount_of_keys, keys = set(), _randint=np.random.randint ):
		logging.info("Generating keys, this may take a while, ...")		
		pickchar = partial( secrets.choice, string.ascii_uppercase \
			.replace("O", "") \
			.replace("I", "") )
		while len(keys) < amount_of_keys:
			keys |= {''.join([pickchar() for _ in range(6)]) for _ in range(amount_of_keys - len(keys))}
		logging.info( "... generated")
		return keys
		
	def assignKeys(self, keys):
		logging.info("Assigning keys to users ...")
		keys = keys.copy()
		
		if len(self.userdata):
		
			for group in self.userdata.keys():
				for uid in self.userdata[group].keys():
					self.userdata[group][uid]['key'] = keys.pop()
		
		logging.info("... done")
	
	def formattedOutput(self):
		for group in sorted( self.userdata.keys() ):
			
			f = open( self.outputDir + "/" + str(group) + ".html", 'w')
			html = "<html>\n<head>\n<title>{title}</title>\n<style>\n{css}\n</style>\n</head>".format( title = group, css = "@page { size: 21cm 29.7cm; margin: 15mm 15mm 15mm 15mm;} table, th, td {border: 1px solid black; border-collapse: collapse; padding: 5pt;} body{font-family: Arial, sans-serif; font-size: 16pt;" )
			html += "<body>\n<h1>Klasse: {group}</h1>\n<table style='width: 100%; border: 1px;'>\n<thead>\n<tr>\n<th><b>Nachname</b></th><th><b>Vorname</b></th><th><b>Schl&uuml;ssel</b></th>\n</tr>\n</thead><tbody>".format( group=group)
			for uid, user in sorted( self.userdata[group].items(), key=lambda u: u[1]['name'] ):
				html += "\n<tr>\n<td>{name}</td><td>{prename}</td><td>{key}</td>\n</tr>".format( name=user['name'], prename=user['prename'], key=user['key'] )
			
			html += "\n</tbody>\n</table>\n</body>\n</html>"
			f.write(html)
			f.close()
			
	def welcome(self):
		ret = False		
		print( "-------- Welcome to KEY GENERATOR --------" )
		print( "This program can generate unique keys for a list of users.")
		print( "The program needs: A list of users as .csv format following this layout:" ) 
		print( "\n\tID,LAST NAME, PRENAME, GROUP\n" )
		print( "hint: you can put the names and group into \" brackets for showing this is one string. Like 1, \"Jon Maria Jack\", \"Doe\"" )
		
		# excel tutorial
		if self.ask( "Do you need help converting your excel sheet into .csv format?", ["y", "n"] ) == "y":
			print( "1. Remove all leading and tailing rows. Also the ones including your table description (like nr, name, prename, group, ...)." )
			print( " There should only be the columns with users data." )
			print( "2. Select File > Save as > select comma seperated values (.csv) on the bottom right of opening window inside file format selector." )
			print( "3. Save your file as input.csv\n" )
			
		print( "Upload your input.csv file with input users data and if you have keys.txt to directory " + self.inputDir + "." )
		
		# upload tutorial
		if self.ask( "Do you need help with uploading?", ["y", "n"] ) == "y":
			print( "- You can simply drag and drop you files from your directory on pc inside your browser. Release them above " + self.inputDir + " directory." )
			print( "- Otherwise you can click the three dots above files list and select Upload File." )
			print( " Upload your file. It will appear outside " + self.inputDir + " directory. Use drag and rop o move it here." )
			
		# continue
		if self.ask( "Do you uploaded as input.csv file, correctly formatted (like emaple above) and optional a keys.txt into " + self.inputDir + "?", ["y", "n"] ) == "y":
			print( "Fine! That's all. The program will continue shortly.\n" )
			print( "The users will get extracted from your input.csv file and unique, crypotraphic safe keys will be assigned to them.\n" )
			print( "The program will generate output file in " + self.outputDir + " directory." )
			print( "For every group in your users data, there will be a .html file with a list of which user has which key." )
			print( "You can normally open them with double click inside your web browser and directly print them." )
			print( "The program will also generate a keys.txt file, containing all the generated keys." )
			print( "You can use this keys.txt inside " + self.inputDir + " directory next time you use this program." )
			print( "The program than will not generate new keys, that are the same as the old keys.\n" )
			print( "DOWNLOAD DATA: After program finished, you can download all data:" )
			print( "1. Click the three dots above files list and select Download as zip" )
			print( "2. Save zip on your computer and unzip it." )
			print( "3. Take a look inside the unzipped content. You find the whole program, with generated output here!" )
			ret = True

		print( "------------------------------------------" )
		return ret
		
	def ask(self, msg="", choices=[]):
		selected = ""
		while True:
			print( "\n\t# " + msg)
			selected = input( "\t" + str(choices) + ": " )
			if selected in choices:
				break
		
		print("")
		return selected
		
if __name__ == "__main__":
	logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

	main = Main( inputDir, outputDir, inputFile, usedKeysFile )
	if main.welcome():
		main.start()
	
	
