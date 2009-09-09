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
from os import urandom,getenv,sep
from optparse import OptionParser
from getpass import getpass

def parseOpts( ):
	parser = OptionParser( version="%prog 0.1-pre", usage="%prog [options] [description|keywords]" )
	parser.add_option( "-a", "--add", action="store_true", dest="add", help="Add a password to the stored passwords" )
	parser.add_option( "-f", "--file", dest="file", default=getenv( 'HOME' )+sep+".passwd" , 
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
	return b64encode( urandom( length ))[ :length ]


if __name__ == "__main__":
	main( *parseOpts( ) )
