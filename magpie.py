#!/usr/bin/env python

#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	 This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

from Crypto.Cipher import AES
from hashlib import sha256
from base64 import b64encode,b64decode
import os 
import sys
from optparse import OptionParser
from getpass import getpass
import subprocess
from tempfile import mkstemp
from time import sleep
import zlib
import re

#	To Do: 
#		add an --edit option
#		add the ability to --force certain types of characters
#		add an --append option as an alternative to --import
#		add an --interactive option?
#		consider the symbols @% for password generation
#		add a --sub option for substituting characters in the generated password

def parseOpts( ):
	parser = OptionParser( version="%prog 0.1-alpha-2009.09.24", usage="%prog [options] [description|keywords]" )
	parser.add_option( "-a", "--add", dest="username", 
		help="Add a password to the stored passwords with the specified username" )
	parser.add_option( "-f", "--file", dest="file", default=os.getenv( 'HOME' )+os.sep+".magpie"+os.sep+"database" , 
		help="Use FILE instead of %default for storing/retrieving passwords" )
	parser.add_option( "-g", "--generate", dest="generate", default=0, type="int",
		help="Generate a random password of the specified length instead of prompting for one" )
	parser.add_option( "-r", "--remove", action="store_true", dest="remove", 
		help="Remove specific password(s) from the database" )
	parser.add_option( "-u", "--user", action="store_true", dest="get_user",
		help="Retrieve the username instead of the password for the account" ),
	parser.add_option( "--debug", action="store_true", help="Print debugging messages to stderr" )
	parser.add_option( "--list", action="store_true", dest="print_all", 
		help="Print entire database to standard output with the passwords masked" )
	parser.add_option( "--change-password", action="store_true", dest="change",
		help="Change the master password for the database" )
	parser.add_option( "--find", action="store_true", dest="find",
		help="Find an entry in the database and print its value with the password masked" )
#	parser.add_option( "-e", "--edit", action="store_true", dest="edit",
#		help="Edit the file in the default system text editor and import the result as the new database" )
	parser.add_option( "--export", dest="exportFile", 
		help="Export the password database to a delimited text file. Keep this file secure, as it will contain " +
		"all of your passwords in plain text. Specify - as the filename to print to stdout." )
	parser.add_option( "--import", dest="importFile",
		help="Import a password database from a delimited text file. This will overwrite any passwords in your " +
		"current database. Specify - as the filename to read from stdin" );
	parser.add_option( "-p", "--print", action="store_true", dest="print_", 
		help="Print the password to standard output instead of copying it to the clipboard" )

	return parser.parse_args( )


def main( options, args ):
	clipboard = Clipboard( )
	if options.generate and not options.username:
		if options.print_:
			sys.stdout.write( PasswordDB.generate( options.generate ))
		else:
			clipboard.write( PasswordDB.generate( options.generate ))
		sys.exit( 0 )
	# prompt for password
	password = getpass( "Master Password: " )

	#Remove the old file if it exist and we are importing new data.
	if options.importFile and os.path.exists( options.file ):
		os.remove( options.file )

	try:
		pdb = PasswordDB( options.file, password )
	except ValueError,e:
		sys.stderr.write( str( e ) + '\n' )
		sys.exit( -1 )

	if options.change:
		newPass       = getpass( "Enter new master password: " )
		newPassVerify = getpass( "Re-enter password: " )
		while not( newPass == newPassVerify ):
			print( "\nPasswords do not match. please try again" )
			newPass       = getpass( "Enter new master password: " )
			newPassVerify = getpass( "Re-enter password: " )
		pdb.password = newPass
		print( "Master Password Changed" )
		pdb.flush( )
		sys.exit( 0 )

	if options.print_all:
		lines = pdb.dump( ).split( '\n' )
		print( "%20s %8s %s" % PasswordDB.splitLine( lines[ 0 ] ))
		for line in lines[ 1: ]:
			print( "%20s %8s %s" % PasswordDB.splitLine( PasswordDB.mask( line )))
		sys.exit( 0 )

	if options.exportFile:
		if options.exportFile == '-':
			sys.stdout.write( pdb.dump( ) )
		else:
			exportFile = open( options.exportFile, 'w' )
			exportFile.write( pdb.dump( ))
			exportFile.close( )
		sys.exit( 0 )

	if options.importFile:
		if options.importFile == '-':
			pdb.load( sys.stdin.read( ))
		else:
			importFile = open( options.importFile )
			pdb.load( importFile.read( ))
			importFile.close( )
		pdb.flush( )
		sys.exit( 0 )

	if options.remove:
		removed = pdb.remove( *args )
		if removed:
			sys.stderr.write( "Removed the following entry:\n%s\n" % removed)
		else:
			sys.stderr.write( "Unable to locate the specified entry\n" )
		pdb.flush( )

	# BUG remove and add at the same time isn't working properly.
	if options.username:
		if options.generate:
			newPass = PasswordDB.generate( options.generate )
			clipboard.write( newPass )
		else:
			newPass       = getpass( "Enter password for new account: " )
			newPassVerify = getpass( "Re-enter password: " )
			while not( newPass == newPassVerify ):
				print( "\nPasswords do not match. please try again" )
				newPass       = getpass( "Enter password for new account: " )
				newPassVerify = getpass( "Re-enter password: " )
		pdb.add( options.username, newPass, str.join( ' ', args ))
		if options.generate:
			sys.stderr.write( "Generated password saved\n" )
		pdb.flush( )

	# The exit is here to allow a person to add and remove at the same time.
	# In other words, replace an entry.
	if options.remove:
		sys.exit( 0 )
	
	if options.find:
		found = pdb.find( args )
		if found:
			print( pdb.data.split( '\n' )[ 0 ] )
			print( PasswordDB.mask( ))
		else:
			print "Unable to locate entry"

	entry = pdb.find( *args ).split( '\t', 2 )
	if options.get_user:
		requested = entry[ 0 ]
	else:
		requested = entry[ 1 ]

	if options.print_:
		sys.stdout.write( requested )
	else:
		clipboard.write( requested )

	pdb.close( )

class PasswordDB( object ):
	def __init__( self, filename, password ):
		self.filename = filename
		self.password = password
		try:
			self.open( )
			if not ( self.data[ :29 ] == "Username\tPassword\tDescription" ):
				raise ValueError
		except ( zlib.error,ValueError ):
			raise ValueError( "You entered an incorrect password" )
			
	def flush( self ):
		if os.path.exists( self.filename ):
			os.rename( self.filename, self.filename+'~' )
		if not os.path.exists( os.path.dirname( self.filename )):
			os.makedirs( os.path.dirname( self.filename ), 0755 )
		passFile = open( self.filename, 'w', 0600 )
		passFile.write( b64encode( self.encode( zlib.compress( self.data[::-1], 9 ))))
		passFile.close( )
		
	def close( self ):
		self.flush( )

	def open( self ):
		if not ( os.path.exists( self.filename )):
			self.data = "Username\tPassword\tDescription\n"
			return False
		passFile = open( self.filename, 'r' )
		self.data =  zlib.decompress( self.decode( b64decode( passFile.read( ))))[::-1]
		passFile.close( )
		return True

	def dump( self ):
		return self.data
	
	def load( self, data ):
		data = data.strip( ).split( "\n" )
		self.data = ""
		for i in data:
			self.data += str.join( '\t', PasswordDB.splitLine( i.strip( )) ) + '\n'
		self.data = self.data.strip( )

	def add( self, username, password, description ):
		if not self.data[ -1 ] == '\n':
			self.data += '\n'
		self.data += str.join( '\t', ( username.strip( ), password.strip( ), description.strip( ) ))
	
	def find( self, *keywords ):
		lines = self.data.split( '\n' )
		for i in xrange( 1, len( lines )):
			correctLine = True
			for j in xrange( len( keywords )):
				correctLine = correctLine and ( keywords[ j ].lower( ) in lines[ i ].lower( ) )
			if correctLine:
				return lines[ i ]
		return False
	
	def remove( self, *keywords ):
		found = self.find( *keywords )
		if not found:
			return False
		lines = self.data.split( '\n' )
		returnvalue =  lines.pop( lines.index( found ) )
		self.data = str.join( '\n', lines )
		return returnvalue

	def mask( dbentry ):
		lines = dbentry.split( '\n' )
		for i in xrange( len( lines )):
			newLine = lines[ i ].split( '\t', 2)
			newLine[ 1 ] = '(%d)' % len( newLine[ 1 ])
			lines[ i ] = str.join( '\t', newLine )
		return str.join( '\n', lines )
	mask = staticmethod( mask )

	def encode( self, text ):
		return AES.new( sha256( self.password ).digest( ), AES.MODE_CFB ).encrypt( text )
	
	def decode( self, text ):
		return AES.new( sha256( self.password ).digest( ), AES.MODE_CFB ).decrypt( text )

	def generate( length ):
		# get a random string containing base64 encoded data, replacing /+ with  !_
		return b64encode( os.urandom( length ), "!_" )[ :length ]
	generate = staticmethod( generate )

	def splitLine( line ):
		return tuple( re.split( "(\s*\t\s*)+", line, 2 )[::2] )
	splitLine = staticmethod( splitLine )

class Clipboard( object ):
	def __init__( self, backend=None ):
		object.__init__( self )
		if backend:
			self.backend = backend
		else:
			backends = dict( )
			if len( subprocess.Popen([ "which", "xsel" ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE ).stdout.read( )):
				self.backend = 'xsel'
			elif len( subprocess.Popen([ "which", "xclip" ], stdout=subprocess.PIPE, 
				stderr=subprocess.PIPE ).stdout.read( )):
				self.backend = 'xclip'

			# to do: check for Tk, Wx, Win32, etc.
	
	def read( self ):
		"""
		Returns the contents of the clipboard
		"""
		if self.backend == 'xsel':
			return subprocess.Popen([ 'xsel', '-o' ], stdout=subprocess.PIPE,).stdout.read( )
		if self.backend == 'xclip':
			return subprocess.Popen([ 'xclip', '-o' ], stdout=subprocess.PIPE,).stdout.read( )
			

	def write( self, text ):
		"""
		Copies text to the system clipboard
		"""
		if self.backend == 'xsel':
			# copy to both XA_PRIMARY and XA_CLIPBOARD
			proc = subprocess.Popen([ 'xsel', '-p', '-i' ], stdout=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			proc = subprocess.Popen([ 'xsel', '-b', '-i' ], stdout=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			return
		if self.backend == 'xclip':
			# copy to both XA_PRIMARY and XA_CLIPBOARD
			proc = subprocess.Popen([ 'xclip', '-selection', 'primary', '-i' ], stdout=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			proc = subprocess.Popen([ 'xclip', '-selection', 'clipboard', '-i' ], stdout=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			return
			
	def clear( self ):
		"""
		Clear the clipboard contents
		"""
		if self.backend == 'xsel':
			subprocess.call([ 'xsel', '-pc' ])
			subprocess.call([ 'xsel', '-bc' ])
			return
		if self.backend == 'xclip':
			proc = subprocess.Popen([ 'xclip', '-i', '-selection', 'primary' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( '' )
			proc.stdin.close( )
			proc.wait( )
			proc = subprocess.Popen([ 'xclip', '-i', '-selection', 'clipboard' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( '' )
			proc.stdin.close( )
			proc.wait( )
			return

	def close( self ):
		pass

if __name__ == "__main__":
	options, args = parseOpts( )
	main( options, args )
