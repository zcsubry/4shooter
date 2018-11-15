#!/usr/bin/env python
#=============================================================================

import struct
import socket
import time
from optparse import OptionParser

#=============================================================================
# Device
#=============================================================================
#
# Class: TCPDevice
#
# This is a base class for various devices connected to the 4shooter
# electronics.  It contains the fundamental TCP communication and command
# building and parsing functions as well ass all basic commands which are
# shared by all devices.
#
# The inherited classes should implement device specific functions.
#
#=============================================================================

class TCPDevice(object):

#-----------------------------------------------------------------------------
# Device::__init__
# Description:
#	Class constructor function.
#-----------------------------------------------------------------------------

	def __init__(self):
		self.host = None
		self.port = None
		self.socket = None
		self.timeout = {}
		self.timeout['default'] = 120
		self.formatstr = ''
		return

#-----------------------------------------------------------------------------
# Device::set
# Synopsis:
#	Device::set host port
# Input:
#	- host (%s):
#		Hostname or IP address of the device
#	- port (%d):
#		Port number of the device
# Description:
#	Set the host and port of the device.
#-----------------------------------------------------------------------------

	def set_port(self, host=None, port=None):
		self.host = host
		self.port = int(port)
		return

#-----------------------------------------------------------------------------

#=============================================================================
# TCP port functions
#=============================================================================

#-----------------------------------------------------------------------------
# Device::connect
# Description:
#	Creates a client socket and connects tries to connect to the server
#	device.
# Return:
#	- True:
#		Connection establishe
#	- False:
#		Connection failed.
#-----------------------------------------------------------------------------

	def connect(self):
		if self.socket is not None:
			return True
		try:
			self.socket = socket.create_connection((self.host, self.port),
					timeout=1)
		except socket.error as msg:
			if self.socket is not None:
				self.socket.close()	
				self.socket = None	
			return False
		self.socket.setblocking(0)
		return True

#-----------------------------------------------------------------------------
# Device::disconnect
# Description:
#	Disconnect from the device server.
#-----------------------------------------------------------------------------

	def disconnect(self):
		if self.socket is not None:
			self.socket.close()
			self.socket = None
		return

#-----------------------------------------------------------------------------
# Device::is_connected
# Description:
#	Checks if the TCP connection to the device is established.
# Return:
#	- True/False
#-----------------------------------------------------------------------------

	def is_connected(self):
		return self.socket is not None

#-----------------------------------------------------------------------------
# Device::write
# Synopsis:
#	Device::write str
# Input:
#	-	str (%s):
#			String to be sent to the server.
# Description:
#	Send $str to the device socket.
# Return:
#	- True:
#		Write succesful.
#	- False:
#		Write failed
#-----------------------------------------------------------------------------

	def write(self, str):
		if self.socket is None:
			return False
		try:
			self.socket.sendall(str)
		except:
			return False
		return True

#-----------------------------------------------------------------------------
# Device::read
# Description:
#	Read the buffer of the device socket and returns the received data.
# Return:
#	- String containing the device response
#-----------------------------------------------------------------------------

	def read(self):
		try:
			rcv = self.socket.recv(1024).rstrip('\n')
		except:
			rcv = None
		return rcv

#-----------------------------------------------------------------------------

#=============================================================================
# Command formatting
#=============================================================================

#-----------------------------------------------------------------------------
# Device::set_format
# Synopsis:
#	set_format str
# Input:
#	- str (%s):
#		Format string
# Description:
#	Define the format of the command to be set to the  device. The string
#	has to contain '%s'.
#-----------------------------------------------------------------------------

	def set_format(self, str):
		self.formatstr = str
		return

#-----------------------------------------------------------------------------
# Device::command
# Synopsis:
#	Device::command cmd
#	- cmd (%s):
#		TCP command to be sent to the device.
# Description:
#	Convert to the input cmd into the proper ascii format and send it to the
#	tcp socket.
#-----------------------------------------------------------------------------

	def command(self, cmd):
		acmd = self.formatstr % (cmd,)
		return self.write(acmd)

#-----------------------------------------------------------------------------
# Device::command_read
# Synopsis:
#	Device::command_read cmd
#	- cmd (%s):
#		Command to be sent to the device either in ascii or in byte list
#		format.
# Description:
#	Convert to the input cmd into the proper ascii format and send it to the
#	tcp socket. Tries to read the socket for response.
# Return:
#	Response of the device.
#-----------------------------------------------------------------------------

	def command_read(self, cmd, sleep=0.3):
		if not self.command(cmd):
			return False
		time.sleep(sleep)
		rcv = self.read()
		if rcv:
			rcv = rcv.rstrip('#\r').lstrip('=')
		return rcv

#-----------------------------------------------------------------------------

#=============================================================================
# Utility functions
#=============================================================================

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

	def get_timeout(self, cmd):
		if cmd in self.timeout:
			return self.timeout[cmd]
		return self.timeout['default']

#-----------------------------------------------------------------------------
# TCPDevice::waitfor
# Synopsis:
#	waitfor method condition value timeout poll init debug
# Input:
# Description:
#	Wait until a certain condition is fullfilled, or timeout occurs.  In
#	each iteration the return value of $method and the value of $value is
#	compared, according to the relatiod defined in $condition.  If the
#	condition is fullfilled, the function returns True.  If the maximum
#	allowed time defined in $timeout is passed, returns False,
#-----------------------------------------------------------------------------

def waitfor(method, condition, value, timeout=30.0, poll=0.2, init=0.2, 
		debug=False):
	end = time.time() + timeout
	if init > 0.0:
		time.sleep(init)
	while time.time() < end:
		ret = method()
		e = 'ret %s value' % condition
		status = eval(e)
		if debug:
			print e, ret, value, status
		if status:
			return True
		time.sleep(poll)
	return False

#-----------------------------------------------------------------------------

#=============================================================================
