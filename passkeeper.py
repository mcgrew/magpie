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
from hashlib import sha1

def main( ):
	pass

def encode( data, password ):
	return  AES.new( sha1( password ).digest( )[ :16 ], AES.MODE_CFB ).encrypt( data )
	
def decode( data, password ):
	return AES.new( sha1( password ).digest( )[ :16 ], AES.MODE_CFB ).decrypt( data )

