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
from base64 import b64encode
from os import urandom
from math import ceil

def main( ):
	pass

def encode( data, password ):
	return  AES.new( sha256( password ).digest( ), AES.MODE_CFB ).encrypt( data )
	
def decode( data, password ):
	return AES.new( sha256( password ).digest( ), AES.MODE_CFB ).decrypt( data )

def generate( length=512 ):
	return b64encode( urandom( length ))[ :length ]

