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
import os.path
import sys
from optparse import OptionParser
from getpass import getpass
import subprocess
from tempfile import mkstemp
from time import sleep

def parseOpts( ):
	parser = OptionParser( version="%prog 0.1-pre", usage="%prog [options] [description|keywords]" )
	parser.add_option( "-a", "--add", dest="username", 
		help="Add a password to the stored passwords with the specified username" )
	parser.add_option( "-f", "--file", dest="file", default=os.getenv( 'HOME' )+os.sep+".passwd" , 
		help="Use FILE instead of %default for storing/retrieving passwords" )
	parser.add_option( "-g", "--generate", action="store_true", dest="generate", 
		help="Generate a random password instead of prompting for one" )
	parser.add_option( "-l", "--length", dest="length", default=16, type="int",
		help="The length for the generated password. Defaults to %default" )
	parser.add_option( "-r", "--remove", action="store_true", dest="remove", 
		help="Remove specific password(s) from the database" )
	parser.add_option( "-u", "--user", action="store_true", dest="get_user",
		help="Retrieve the username instead of the password for the account" ),
	parser.add_option( "--debug", action="store_true",
		help="Print debugging messages to stderr" )
	parser.add_option( "--all", action="store_true", dest="print_all", 
		help="Print entire database to standard output. Make sure no one is watching!" )
	parser.add_option( "--find", action="store_true", dest="find",
		help="Find an entry in the database and print its value with the password masked" )
#	parser.add_option( "-e", "--edit", action="store_true", dest="edit",
#		help="Edit the file in the default system text editor and import the result as the new database" )
	parser.add_option( "--export", dest="exportFile", 
		help="Export the password database to a delimited text file. Keep this file secure, as it will contain " +
		"all of your passwords in plain text." )
	parser.add_option( "--import", dest="importFile",
		help="Import a password database from a delimited text file. This will overwrite any passwords in your " +
		"current database" );
	parser.add_option( "--print", action="store_true", dest="print_", 
		help="Print the password to standard output instead of copying it to the clipboard" )

	return parser.parse_args( )


def main( options, args ):
	# prompt for password
	password = getpass( "Password: " )
	clipboard = Clipboard( )

	#Remove the old file if it exist and we are importing new data.
	if options.importFile and os.path.exists( options.file ):
		os.remove( options.file )

	try:
		pdb = PasswordDB( options.file, password )
	except ValueError,e:
		sys.stderr.write( str( e ) + '\n' )
		sys.exit( -1 )

	if options.print_all:
		print( pdb.export( ))
		sys.exit( 0 )

	if options.exportFile:
		if options.exportFile == '-':
			sys.stdout.write( pdb.export( ) )
		else:
			exportFile = open( options.exportFile, 'w' )
			exportFile.write( pdb.export( ))
			exportFile.close( )
		sys.exit( 0 )

	if options.importFile:
		if options.importFile == '-':
			pdb.import_( sys.stdin.read( ))
		else:
			importFile = open( options.importFile )
			pdb.import_( importFile.read( ))
			importFile.close( )
		pdb.close( )
		sys.exit( 0 )

	if options.username:
		if options.generate:
			newPass = generate( options.length )
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
			
	if options.remove:
		sys.stderr.write( "Removed the following entry:\n"+pdb.remove( *args ))
		pdb.close( )
		sys.exit( 0 )
	
	if options.find:
		print( pdb.data.split( '\n' )[ 0 ] )
		print( PasswordDB.mask( pdb.find( )))

	entry = pdb.find( *args ).split( '\t', 2 )
	if options.get_user:
		requested = entry[ 0 ]
	else:
		requested = entry[ 1 ]

	if options.print_:
		print( entry[ 0 ] )
	else:
		clipboard.write( entry[ 0 ] )


	pdb.close( )

class PasswordDB( object ):
	def __init__( self, filename, password ):
		self.filename = filename
		self.password = password
		self.open( )
		if not ( self.data[ :29 ] == "Username\tPassword\tDescription" ):
			if options.debug:
				sys.stderr.write( "PasswordDB appeared to contain:\n"+self.data+"\n" )
			raise ValueError( "You entered an incorrect password" )
			

	def close( self ):
		passFile = open( self.filename, 'w' )
		passFile.write( self.cipher.encrypt( self.data ))
		passFile.close( )
		
	def open( self ):
		if not ( os.path.exists( self.filename )):
			self.data = "Username\tPassword\tDescription\n"
			return False
		passFile = open( options.file, 'r' )
		self.data =  self.cipher.decrypt( passFile.read( ))
		passFile.close( )
		return True

	def export( self ):
		return self.data
	
	def import_( self, data ):
		self.data = data.strip( )
		while( "\t\t" in self.data ):
			self.data = self.data.replace( "\t\t", "\t" )

	def add( self, username, password, description ):
		self.data += "%s\t%s\t%s" % ( username, password, description )
	
	def find( self, *keywords ):
		lines = self.data.split( '\n' )
		for i in xrange( len( lines )):
			for j in xrange( len( keywords )):
				if not ( keywords[ j ] in lines[ i ] ):
					continue
			return lines[ i ]
		return False
	
	def remove( self, *keywords ):
		lines = self.data.split( '\n' )
		for i in xrange( len( lines )):
			for j in xrange( len( keywords )):
				if not ( keywords[ j ] in lines[ i ] ):
					continue
			returnvalue =  lines.pop( i )
			self.data = str.join( '\n', lines )
			return returnvalue
		return False

	def mask( dbentry ):
		lines = dbentry.split( '\n' )
		for i in xrange( len( lines )):
			newLine = lines[ i ].split( '\t', 2)
			newLine[ 1 ] = '*' * len( newLine[ 1 ])
			lines[ i ] = str.join( '\t', newLine )
		return str.join( '\n', lines )
	mask = staticmethod( mask )

	def encode( self, text ):
		return AES.new( sha256( self.password ).digest( ), AES.MODE_CFB ).encrypt( text )
	
	def decode( self, text ):
		return AES.new( sha256( self.password ).digest( ), AES.MODE_CFB ).decrypt( text )

	def generate( length=512 ):
		# get a random string containing base64 encoded data, replacing /+ with  !_
		return b64encode( os.urandom( length ), "!_" )[ :length ]
	generate = staticmethod( generate )

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
			return subprocess.Popen([ 'xsel', '-o' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE ).stdout.read( )
		if self.backend == 'xclip':
			return subprocess.Popen([ 'xclip', '-o' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE ).stdout.read( )
			

	def write( self, text ):
		"""
		Copies text to the system clipboard
		"""
		if self.backend == 'xsel':
			# copy to both XA_PRIMARY and XA_CLIPBOARD
			proc = subprocess.Popen([ 'xsel', '-pi' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			proc = subprocess.Popen([ 'xsel', '-bi' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			return
		if self.backend == 'xclip':
			# copy to both XA_PRIMARY and XA_CLIPBOARD
			proc = subprocess.Popen([ 'xclip', '-selection', 'primary', '-i' ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE )
			proc.stdin.write( text )
			proc.stdin.close( )
			proc.wait( )
			proc = subprocess.Popen([ 'xclip', '-selection', 'clipboard', '-i' ], stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, stdin=subprocess.PIPE )
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
