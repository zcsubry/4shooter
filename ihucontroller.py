#!/usr/bin/env python
#=============================================================================

import tcpdevice

import subprocess
from optparse import OptionParser
from os import environ

#=============================================================================
# Class: IHUcontroller
#=============================================================================

class IHUcontroller(tcpdevice.TCPDevice):

#-----------------------------------------------------------------------------
# IHUcontroller::__init__
# Description:
#	Class constructor function.
#-----------------------------------------------------------------------------

	def __init__(self, nmotor=24):
		tcpdevice.TCPDevice.__init__(self)
		self.set_format(':%s#\n')
		self.nmotor = nmotor
		return

#-----------------------------------------------------------------------------

#=============================================================================
# Command building functions
#
# These functions are to parsing the input motor and argumen lists and build
# the command string to be sent to the controller.
#=============================================================================

#-----------------------------------------------------------------------------
# IHUcontroller::get_id
#-----------------------------------------------------------------------------

	def get_ids(self, ids=None, listonly=False):
		if ids is None:
			ids = [x+1 for x in range(self.nmotor)]
		elif type(ids) is tuple:
			ids = list(ids)
		elif type(ids) is list:
			ids = ids
		elif listonly:
			ids = [ids]
		else:
			ids = ids
		return ids

#-----------------------------------------------------------------------------
# IHUcontroller::motor_bit
#-----------------------------------------------------------------------------

	def motor_bit(self, ids=None):
		ids = self.get_ids(ids, listonly=True)
		if ids is None:
			bitlist = ['1' for x in range(self.nmotor,0,-1)]
		else:
			bitlist = ['1' if x in ids else '0' for x in range(self.nmotor,0,-1)]
		bits = '0b' +  ''.join(bitlist)
		return bits

#-----------------------------------------------------------------------------
# IHUcontroller::motor_result
#-----------------------------------------------------------------------------

	def motor_result(self, rbits, ids=None):
		mbits = self.motor_bit(ids);
		rbits1 = rbits[::-1]
		mbits1 = mbits[::-1]
		result = []
		for rbit, mbit in zip(rbits1,mbits1):
			if mbit == '1':
				result.append(int(rbit))
		return result

#-----------------------------------------------------------------------------
# IHUcontroller::build_command
#-----------------------------------------------------------------------------

	def build_command(self, cmd, motors=None, args=''):
		motors = self.get_ids(motors)
		args = self.get_ids(args)
		if type(motors) is list and args == '':
			cmd += 'M'
			motorid = self.motor_bit(motors)
			arg = ''
		elif type(motors) is list and type(args) is list:
			cmd += 'I'
			motorid = self.motor_bit(motors)
			args.reverse()
			arg = ', '.join([str(x) for x in args])
		elif type(motors) is list:
			cmd += 'C'
			motorid = self.motor_bit(motors)
			arg = str(args)
		else:
			cmd += 'S'
			motorid = str(motors)					
			if type(args) is list:
				args = args[0]
			arg = str(args)

		cmdstr = "%s %s %s" % (cmd, motorid, arg)
		return cmdstr.strip()

#-----------------------------------------------------------------------------

#=============================================================================
# Controller initialization and motor setting commands
#=============================================================================

#-----------------------------------------------------------------------------
# IHUcontroller:init
# Description:
#	Initialize the controller unit. If $ids specified, then initialize the 
#	motors attached to the selected port.
#-----------------------------------------------------------------------------

	def init(self, ids=None):
		if not ids:
			cmd = 'I'
			rcv = self.command_read(cmd) 
		else:
			ids = self.get_ids(ids)
			for id in ids:
				cmd = 'II %d' % id
				rcv = self.command_read(cmd) 
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::init_all
# Description:
#	Initialize the controller and all ports in one command.
#-----------------------------------------------------------------------------

	def init_all(self, id=None):
		self.init()
		for i in range(1,9):
			self.init(i)

#-----------------------------------------------------------------------------
# IHUcontroller::get_motor_wiring
# Description:
#	Return the wiring info of the selected motors.  The wiring bit is 0 for
#	normal, and 1 for reverse wiring.
#-----------------------------------------------------------------------------

	def get_motor_wiring(self, ids=None, raw=False):
		rcv = self.command_read('GMWB')
		wbits = '0b' + rcv[-24:]
		if raw:
			return wbits
		ids = self.get_ids(ids, listonly=True)
		result = self.motor_result(wbits, ids)
		return result

#-----------------------------------------------------------------------------
# IHUcontroller::set_motor_wiring
# Description:
#	Change the wiring (rotation direction) of the selected motors.  The
#	wiring bit is 0 for normal and 1 for reverse wiring.
#-----------------------------------------------------------------------------

	def set_motor_wiring(self, ids, bits):
		rcv = self.get_motor_wiring(raw=True)[-24:]
		cbits = [int(x) for x in list(rcv)]
		ids = self.get_ids(ids, listonly=True)
		if ids is None:
			ids = [x for x in range(1, self.nmotor+1)]
		if type(bits) is not list:
			nbits = [bits for x in ids]
		else:
			nbits = bits
		bitlist = dict(zip(ids, nbits))
		for id,bit in bitlist.iteritems():
			cbits[self.nmotor-id] = bit
		bitstr = ''.join([str(x) for x in cbits])
		cmd = "SMW 0b%s" % bitstr
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::motor_wake
# Description:
#	Wake up the selected motors.
#-----------------------------------------------------------------------------

	def motor_wake(self, ids=None):
		bits = self.motor_bit(ids)
		cmd = 'MW %s' % bits
		rcv = self.command_read(cmd)
		return rcv
		
#-----------------------------------------------------------------------------
# IHUcontroller::motor_wake
# Description:
#	Send the selected motors to sleep.
#-----------------------------------------------------------------------------

	def motor_sleep(self, ids=None):
		bits = self.motor_bit(ids)
		cmd = 'MS %s' % bits
		rcv = self.command_read(cmd)
		return rcv
		
#-----------------------------------------------------------------------------

#=============================================================================
# Low level motor move commands
#=============================================================================

#-----------------------------------------------------------------------------
# IHUcontroller::motor_move
# Description:
#	Start free moving of the selected motors in normal or reverse direction.
#-----------------------------------------------------------------------------

	def motor_move(self, id, reverse=False):
		if not reverse:
			cmd = 'MF %d' % id
		else:
			cmd = 'MB %d' % id
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::motor_stop
# Description:
#	Stop the movement of the selected motors.
#-----------------------------------------------------------------------------

	def motor_stop(self, id):
		cmd = 'MQ %d' % id
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::motor_relative
# Description:
#	Move the selected motors relative to its current position.
#-----------------------------------------------------------------------------

#	def motor_relative(self, id, steps):
#		cmd = 'MR %d %d' % (id, step)
#		rcv = self.command_read(cmd)
#		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::get_motor_status
# Description:
#	Return the current status of the selected motors.
#-----------------------------------------------------------------------------

	def get_motor_status(self, ids=None):
		cmd = 'GMSA'
		rcv = self.command_read(cmd)
		sbits = rcv[::-1]
		status = self.motor_result(sbits, ids)		
		return status

#-----------------------------------------------------------------------------
# IHUcontroller::get_motor_position
# Description:
#	Return the current position of the selected motors.
#-----------------------------------------------------------------------------

	def get_motor_position(self, ids=None):
		cmd = self.build_command('GMP', ids)
		rcv = self.command_read(cmd)
		pos = [int(x) for x in rcv.split(',')]
		return pos

#-----------------------------------------------------------------------------
# IHUcontroller::get_motor_target
# Description:
#	Return the target position of the selected motors
#-----------------------------------------------------------------------------

	def get_motor_target(self, ids=None):
		cmd = self.build_command('GMT', ids)
		rcv = self.command_read(cmd)
		pos = [int(x) for x in rcv.split(',')]
		return pos

#-----------------------------------------------------------------------------
# IHUcontroller::set_motor_position
# Description:
#	Set the current position counter of the selected motors.
#-----------------------------------------------------------------------------

	def set_motor_position(self, ids, pos):
		cmd = self.build_command('SMP', ids, pos)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::set_motor_target
# Description:
#	Set the target position of the selected motors.
#-----------------------------------------------------------------------------

	def set_motor_target(self, ids, pos):
		cmd = self.build_command('SMT', ids, pos)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::motor_goto
# Description:
#	Move the selected motors to the target position.
#-----------------------------------------------------------------------------

	def motor_goto(self, ids=None):
		bits = self.motor_bit(ids)
		cmd = 'MGC %s' % bits
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# IHUcontroller::motor_settle
# Description:
#	Wait until the selected motors are settled down (finish moving) or
#	timeout occurs.
#-----------------------------------------------------------------------------

	def motor_settle(self, ids=None, timeout=10):
		
		def get_status():
			return self.get_motor_status(ids)

		ids = self.get_ids(ids, listonly=True)
		status = [0 for x in ids]
		return tcpdevice.waitfor(get_status, '==', status, timeout=timeout)

#-----------------------------------------------------------------------------

#=============================================================================
# High level motor control commands
#=============================================================================

#-----------------------------------------------------------------------------
# IHUcontroller::motor_new
# Description:
#	Move the selected motors to the new positions.  If $wait is True, then
#	wait until the motors are settled.
#-----------------------------------------------------------------------------

	def motor_new(self, ids=None, pos=0, wait=True):
		rcv = self.set_motor_target(ids, pos)
		rcv = self.motor_goto(ids)
		if not wait:
			return rcv
		self.motor_settle(ids)
		return self.motor_get(ids)

#-----------------------------------------------------------------------------
# IHUcontroller::motor_make
#	Move the selected motors relative to their current positions.  If $wait
#	 is True, then wait until the motors are settled.
#-----------------------------------------------------------------------------

	def motor_make(self, ids=None, pos=0, wait=True):
		pos = self.get_ids(pos)
		pos0 = self.motor_get(ids)
		if type(pos) is list:
			pos1 = [sum(x) for x in zip(pos, pos0)]
		else:
			pos1 = [x+pos for x in pos0]
		return self.motor_new(ids, pos1, wait)

#-----------------------------------------------------------------------------
# IHUcontroller::motor_get
# Descriptions:
#	Return the current position of the selected motors.
#-----------------------------------------------------------------------------

	def motor_get(self, ids=None):
		return self.get_motor_position(ids)

#-----------------------------------------------------------------------------
# IHUcontroller::motor_set
# Description:
#	Set the current position counter of the selected motors.
#-----------------------------------------------------------------------------

	def motor_set(self, ids=None, pos=0):
		self.set_motor_position(ids, pos)
		self.set_motor_target(ids, pos)
		return self.get_motor_position(ids)

#-----------------------------------------------------------------------------
# IHUcontroller::motor_reset
# Description:
#	Reset the current position counter of the selected motors to zero.
#-----------------------------------------------------------------------------

	def motor_reset(self, ids=None):
		return self.motor_set(ids, 0)

#-----------------------------------------------------------------------------

#=============================================================================

class IHU(object):

#-----------------------------------------------------------------------------
# IHU::__init__
#-----------------------------------------------------------------------------

	def __init__(self, controller, alt, alm, foc):
		self.controller = controller
		self.motor_id = {}
		self.motor_id['alt'] = int(alt)
		self.motor_id['alm'] = int(alm)
		self.motor_id['foc'] = int(foc)
		return

#-----------------------------------------------------------------------------
# IHU::get_motor_id
#-----------------------------------------------------------------------------

	def get_motor_id(self, axis):
		return self.motor_id[axis]

#-----------------------------------------------------------------------------
# IHU::get_result
#-----------------------------------------------------------------------------

	def get_result(self, ret):
		if type(ret) is list or type(ret) is  tuple:
			return ret[0]
		return ret

#-----------------------------------------------------------------------------
# IHU::move
#-----------------------------------------------------------------------------

	def move(self, axis, reverse=False):
		id = self.get_motor_id(axis)
		return self.controller.motor_move(id, reverse)

#-----------------------------------------------------------------------------
# IHU::stop
#-----------------------------------------------------------------------------

	def stop(self, axis):
		id = self.get_motor_id(axis)
		return self.controller.motor_stop(id)

#-----------------------------------------------------------------------------
# IHU::get_status
#-----------------------------------------------------------------------------

	def get_status(self, axis):
		id = self.get_motor_id(axis)
		ret = self.controller.get_motor_status(id)
		return self.get_result(ret)

#-----------------------------------------------------------------------------
# IHU::get_position
#-----------------------------------------------------------------------------

	def get_position(self, axis):
		id = self.get_motor_id(axis)
		ret = self.controller.motor_get(id)
		return self.get_result(ret)

#-----------------------------------------------------------------------------
# IHU::set_position
#-----------------------------------------------------------------------------

	def set_position(self, axis, pos):
		id = self.get_motor_id(axis)
		ret = self.controller.motor_set(id, pos)
		return self.get_result(ret)

#-----------------------------------------------------------------------------
# IHU::reset_position
#-----------------------------------------------------------------------------

	def reset_position(self, axis):
		id = self.get_motor_id(axis)
		ret = self.controller.motor_set(id, 0)
		return self.get_result(ret)

#-----------------------------------------------------------------------------
# IHU::new
#-----------------------------------------------------------------------------

	def new(self, axis, pos, wait=True):
		id = self.get_motor_id(axis)
		ret = self.controller.motor_new(id, pos, wait)
		return self.get_result(ret)

#-----------------------------------------------------------------------------
# IHU::make
#-----------------------------------------------------------------------------

	def make(self, axis, pos, wait=True):
		id = self.get_motor_id(axis)
		ret = self.controller.motor_make(id, pos, wait)
		return self.get_result(ret)

#-----------------------------------------------------------------------------

#=============================================================================
# Main program (for testing and debugging)
#=============================================================================

#-----------------------------------------------------------------------------
# read_command_line
#-----------------------------------------------------------------------------

def read_command_line():

	parser = OptionParser(usage='%prog [--options]')
	
	parser.add_option('--host', dest='host', default=None,
			action='store', type='str')
	parser.add_option('--port', dest='port', default=None,
			action='store', type='str')
	parser.add_option('-c', dest='controller', default=None,
			action='store', type='int')
	parser.add_option('-i', dest='id', default=None,
			action='store', type='int')
	parser.add_option('--ihu', dest='ihu', default=None,
			action='store', type='int')

	parser.add_option('--alt', dest='altdev', default=False,
			action='store_true')
	parser.add_option('--alm', dest='almdev', default=False,
			action='store_true')
	parser.add_option('--foc', dest='focdev', default=False,
			action='store_true')

	parser.add_option('--init', dest='init', default=False,
			action='store_true')
	parser.add_option('--get', dest='get', default=False,
			action='store_true')
	parser.add_option('--reset', dest='reset', default=False,
			action='store_true')
	parser.add_option('--set', dest='setstr', default=None,
			action='store', type='str')
	parser.add_option('--make', dest='makestr', default=None,
			action='store', type='str')
	parser.add_option('--new', dest='newstr', default=None,
			action='store', type='str')
	

	try:
		options, args = parser.parse_args()
	except Exception, error:
		parser.print_help()
		print error
		exit(1)


	if options.altdev is True:
		options.dev = 'alt'
	elif options.almdev is True:
		options.dev = 'alm'
	elif options.focdev is True:
		options.dev = 'foc'
	else:
		options.dev = None

	str = None
	if options.get is True:
		options.action = 'get'
	elif options.reset is True:
		options.action = 'reset'
	elif options.setstr is not None:
		options.action = 'set'
		str = options.setstr
	elif options.makestr is not None:
		options.action = 'make'
		str = options.makestr
	elif options.newstr is not None:
		options.action = 'new'
		str = options.newstr
	elif options.init is True:
		options.action = 'init'
	else:
		options.action = None

	if options.ihu is not None:
		options.controller, options.id = find_ihu(options.ihu)

	options.target = None
	if str is not None:
		options.target = int(str)

	return options

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def find_ihu(ihu):
	ihus = {}
	ihus[1] = (1,1)
	ihus[2] = (1,2)
	ihus[3] = (1,3)
	ihus[4] = (1,4)
	return ihus[ihu]
	
#-----------------------------------------------------------------------------

if __name__=='__main__' :

	options = read_command_line()
	
	host = '192.168.9.2%d' % options.controller
	port = 5000

	c = IHUcontroller()
	c.set_port(host, port)
	ret = c.connect()

	m1 = (options.id) * 3 - 2
	m2 = m1 + 1
	m3 = m1 + 2
	d = IHU(c, m1, m2, m3)

	dev = options.dev
	action = options.action
	target = options.target

	if action == 'init':
		print c.init_all()
		
	if action == 'set':
		d.set_position(dev, target)
	if action == 'reset':
		d.reset_position(dev)

	if action == 'make':
		d.make(dev, target)
	if action == 'new':
		d.new(dev, target)

	if action in ['get', 'set', 'reset', 'make', 'new']:
		print d.get_position(dev)

#=============================================================================
