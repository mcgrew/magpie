#!/usr/bin/env python

from Crypto.Cipher import AES
from hashlib import sha1

def main( ):
	pass

def encode( data, password ):
	return  AES.new( sha1( password ).digest( )[ :16 ], AES.MODE_CFB ).encrypt( data )
	
def decode( data, password ):
	return AES.new( sha1( password ).digest( )[ :16 ], AES.MODE_CFB ).decrypt( data )

