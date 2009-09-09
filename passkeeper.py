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
from optparse import OptionParser
from getpass import getpass
import subprocess

def parseOpts( ):
	parser = OptionParser( version="%prog 0.1-pre", usage="%prog [options] [description|keywords]" )
	parser.add_option( "-a", "--add", action="store_true", dest="add", help="Add a password to the stored passwords" )
	parser.add_option( "-f", "--file", dest="file", default=os.getenv( 'HOME' )+os.sep+".passwd" , 
		help="Use FILE instead of %default for storing/retrieving passwords" )
	parser.add_option( "-g", "--generate", action="store_true", dest="generate", 
		help="Generate a random password instead of prompting for one" )
	parser.add_option( "-r", "--remove", action="store_true", dest="remove", 
		help="Remove specific password(s) from the database" )
	parser.add_option( "-u", "--user", action="store_true", dest="get_user",
		help="Retrieve the username instead of the password for the account" ),
	parser.add_option( "--all", action="store_true", dest="print_all", 
		help="Print entire database to standard output. Make sure no one is watching!" )
	parser.add_option( "--get", action="store_true", default=True, 
		help="Get a password from the database. This is the default action" )
	parser.add_option( "--print", action="store_true", dest="print", 
		help="Print the password to standard output instead of copying it to the clipboard" )

	return parser.parse_args( )


def main( options, args ):
	# prompt for password
	password = getpass( "Password: " )

def encode( data, password ):
	return  AES.new( sha256( password ).digest( ), AES.MODE_CFB ).encrypt( data )
	
def decode( data, password ):
	return AES.new( sha256( password ).digest( ), AES.MODE_CFB ).decrypt( data )

def generate( length=512 ):
	return b64encode( os.urandom( length ))[ :length ]

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
		Copies to both XA_PRIMARY and XA_CLIPBOARD
		"""
		if self.backend == 'xsel':
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

	close = clear

if __name__ == "__main__":
	main( *parseOpts( ) )
