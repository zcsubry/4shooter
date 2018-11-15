# !/usr/bin/env python
#=============================================================================

import tcpdevice

import time
import re
from optparse import OptionParser

DOME_HOST = '192.168.50.11'
DOME_PORT = 23

DOME_STATUS_STOPPED	= 0
DOME_STATUS_OPENING	= 1
DOME_STATUS_CLOSING	= 2
DOME_STATUS_ERROR =	3

DOME_STATUS_STOPPED_STR	= "stopped"
DOME_STATUS_OPENING_STR	= "opening"
DOME_STATUS_CLOSING_STR	= "closing"
DOME_STATUS_ERROR_STR = "ERROR"

DOME_POSITION_OPENED = 0
DOME_POSITION_CLOSED = 1
DOME_POSITION_UNKNOWN = 2
DOME_POSITION_ERROR	= 3

DOME_POSITION_OPENED_STR = "opened"
DOME_POSITION_CLOSED_STR = "closed"
DOME_POSITION_UNKNOWN_STR = "UNKNOWN"
DOME_POSITION_ERROR_STR = "ERROR"

MOTOR_STATUS_STOPPED = 0
MOTOR_STATUS_OPENING = 1
MOTOR_STATUS_CLOSING = 2
MOTOR_STATUS_ERROR = 3

MOTOR_STATUS_STOPPED_STR = "stopped"
MOTOR_STATUS_OPENING_STR = "opening"
MOTOR_STATUS_CLOSING_STR = "closing"
MOTOR_STATUS_ERROR_STR = "ERROR"

DOME_MODE_FAILSAFE_OFF = 0
DOME_MODE_FAILSAFE_ON = 1
DOME_MODE_ERROR = 2

DOME_MODE_FAILSAFE_OFF_STR = "failsafe off"
DOME_MODE_FAILSAFE_ON_STR = "failsafe on"
DOME_MODE_ERROR_STR = "ERROR"

STATUS_IDX_DOME = 0
STATUS_IDX_POSITION = 1
STATUS_IDX_MOTOR = 2
STATUS_IDX_MODE = 3

STATUS_IDX_OUTPUT_CH = 4
STATUS_IDX_INPUT_HV_CH = 5
STATUS_IDX_INPUT_LV_CH = 6

STATUS_IDX_POSITION_DETECTOR_OPEN = 7
STATUS_IDX_POSITION_DETECTOR_CLOSE = 8

STATUS_IDX_PSU_OK = 9
STATUS_IDX_UPS_OK = 10
STATUS_IDX_BAT_DISCHG = 11
STATUS_IDX_BAT_FAIL = 12
STATUS_IDX_POWER = (9, 10, 11, 12)

STATUS_IDX_MOTOR_CURRENT = 13
STATUS_IDX_MOTOR_CURRENT_LIMIT = 14
STATUS_IDX_MOTOR_CURRENT_MAX_LIMIT = 15
STATUS_IDX_MOTOR_CURRENTS = (13, 14, 15)

STATUS_IDX_PING_WATCHDOG = (16, 17, 18)
STATUS_IDX_RESET_WATCHDOG = (19, 20, 21)

#=============================================================================
# Dome
#=============================================================================
#
# Class: Dome
#
# Class for controlling the dome. The class uses the TCPDevice class in
# order to connect and communicate with the 4shooter dome tcp interface.
#
#=============================================================================

class Dome(tcpdevice.TCPDevice):

#-----------------------------------------------------------------------------
# Dome::__init__
# Description:
#	Class constructor function.
#-----------------------------------------------------------------------------

	def __init__(self):
		tcpdevice.TCPDevice.__init__(self)
		self.set_format('%s\n')

		self.timeout['default'] = 120
		self.timeout['open'] = 180
		self.timeout['close'] = 180

		return

#-----------------------------------------------------------------------------
# Dome::connect
#-----------------------------------------------------------------------------

	def connect(self):
		ret = tcpdevice.TCPDevice.connect(self)
		if not ret:
			return False
		return True

#-----------------------------------------------------------------------------
# Dome::set
#-----------------------------------------------------------------------------

	def set_port(self):
		return tcpdevice.TCPDevice.set_port(self, host=DOME_HOST, port=DOME_PORT)

#-----------------------------------------------------------------------------

#=============================================================================
# Dome open/close commands
#=============================================================================

#-----------------------------------------------------------------------------
# Dome::open
# Description:
#	Open the dome. If $wait is True, then wait until the operation is done
#	(or fails or interrupted).
#-----------------------------------------------------------------------------

	def open(self, wait=True):
		ret = self.send_open()
		if not wait:
			return ret
		
		timeout = self.get_timeout("open")
		ret = tcpdevice.waitfor(self.get_dome_status, '!=',
				DOME_STATUS_OPENING_STR, timeout)
		if not ret:
			return False
			
		ret = self.get_dome_position()
		if ret == DOME_POSITION_OPENED_STR:
			return True
			
		return False

#-----------------------------------------------------------------------------
# Dome::close
# Description:
#	Close the dome. If $wait is True, then wait until the operation is done
#	(or fails or interrupted).
#-----------------------------------------------------------------------------

	def close(self, wait=True):
		ret = self.send_close()
		if not wait:
			return ret
		
		timeout = self.get_timeout("close")
		ret = tcpdevice.waitfor(self.get_dome_status, '!=',
				DOME_STATUS_CLOSING_STR, timeout)
		if not ret:
			return False
			
		ret = self.get_dome_position()
		if ret == DOME_POSITION_CLOSED_STR:
			return True
			
		return False

#-----------------------------------------------------------------------------
# Dome::stop
# Description:
#	Stop the dome.
#-----------------------------------------------------------------------------

	def stop(self):
		ret = self.send_stop()
		return ret

#-----------------------------------------------------------------------------

#=============================================================================
# Status query functions 
#=============================================================================

#-----------------------------------------------------------------------------
# Dome::get_full_status
#-----------------------------------------------------------------------------

	def get_full_status(self, id=None, raw=False):
		return self.get_status_report("full", id, raw)

#-----------------------------------------------------------------------------
# Dome::get_brief_status
#-----------------------------------------------------------------------------

	def get_brief_status(self, id=None, raw=False):
		return self.get_status_report("brief", id, raw)

#-----------------------------------------------------------------------------
# Dome::get_dome_status
# Description:
#	Return the current dome status.
# Return:
#	stopped/opening/closing/ERROR
#-----------------------------------------------------------------------------

	def get_dome_status(self):
		return self.get_brief_status(STATUS_IDX_DOME)

#-----------------------------------------------------------------------------
# Dome::get_dome_position
# Description:
#	Return the current dome position.
# Return:
#	opened/closed/UNKNOWN/ERROR
#-----------------------------------------------------------------------------

	def get_dome_position(self):
		return self.get_brief_status(STATUS_IDX_POSITION)

#-----------------------------------------------------------------------------
# Dome::get_motor_status
# Description:
#	Return the current motor status.
# Return:
#	stopped/opening/closing/ERROR
#-----------------------------------------------------------------------------

	def get_motor_status(self):
		return self.get_brief_status(STATUS_IDX_MOTOR)

#-----------------------------------------------------------------------------
# Dome::get_dome_mode
# Description:
#	Return the current dome failsafe mode
# Return:
#	failsafe on/failsafe off/ERROR
#-----------------------------------------------------------------------------

	def get_dome_mode(self):
		return self.get_brief_status(STATUS_IDX_MODE)

#-----------------------------------------------------------------------------
# Dome::get_output_channels
# Description:
#	Return the status of the 16 output channels. If $channel is specified,
#	thet return only the status of selected output channel.
#-----------------------------------------------------------------------------

	def get_output_channels(self, channel=None):
		return self.get_channels(STATUS_IDX_OUTPUT_CH, channel)

#-----------------------------------------------------------------------------
# Dome::get_input_hv_channels
# Description:
#	Return the status of the 5 high voltage inputchannels.  If $channel is
#	specified, thet return only the status of selected channel.
#-----------------------------------------------------------------------------

	def get_input_hv_channels(self, channel=None):
		return self.get_channels(STATUS_IDX_INPUT_HV_CH, channel)

#-----------------------------------------------------------------------------
# Dome::get_input_lv_channels
# Description:
#	Return the status of the 5 low voltage inputchannels.  If $channel is
#	specified, thet return only the status of selected channel.
#-----------------------------------------------------------------------------

	def get_input_lv_channels(self, channel=None):
		return self.get_channels(STATUS_IDX_INPUT_LV_CH, channel)

#-----------------------------------------------------------------------------
# Dome::get_dome_position_detectors
# Description:
#	Return the status of the 4 dome position detectors.
#-----------------------------------------------------------------------------

	def get_dome_position_detectors(self):
		str1 = self.get_full_status(STATUS_IDX_POSITION_DETECTOR_OPEN)
		str2 = self.get_full_status(STATUS_IDX_POSITION_DETECTOR_CLOSE)
		if str1 is None or str2 is None:
			return None
		r1 = str1.rstrip(',').split(',')
		r2 = str2.rstrip(',').split(',')
		ret  = [int(x) for x in r1 + r2]
		return ret

#-----------------------------------------------------------------------------
# Dome::get_power_status
# Descpription:
#	Return the 4 power status indicators: PSU DC OK, UPS DC OK, BAT DISCHG
#	and BAT FAIL.
#-----------------------------------------------------------------------------

	def get_power_status(self):
		str = self.get_full_status(STATUS_IDX_POWER)
		ret = self.str2int(str)
		return ret

#-----------------------------------------------------------------------------
# Dome::get_motor_current
# Description:
#	Return the motor current and its limits.
#-----------------------------------------------------------------------------

	def get_motor_current(self):
		str = self.get_full_status(STATUS_IDX_MOTOR_CURRENTS)
		ret = self.str2float(str)
		return ret

#-----------------------------------------------------------------------------
# Dome::get_ping_watchdog
# Return the status of the ping watchdog: enabled/disabled, timeout, counter.
#-----------------------------------------------------------------------------

	def get_ping_watchdog(self):
		str = self.get_full_status(STATUS_IDX_PING_WATCHDOG)
		r1 = str[0:1]
		r2 = self.str2int(str[1:3])
		return r1 + r2

#-----------------------------------------------------------------------------
# Dome::get_reset_watchdog
# Destription:
# 	Return the status of the reset watchdog: enabled/disabled, timeout,
# 	counter.
#-----------------------------------------------------------------------------

	def get_reset_watchdog(self):
		str = self.get_full_status(STATUS_IDX_RESET_WATCHDOG)
		r1 = str[0:1]
		r2 = self.str2int(str[1:3])
		return r1 + r2

#-----------------------------------------------------------------------------
# Dome::get_temps
# Description:
#	Return the temperature sensor values in Celsius (outside, inside, motor,
#	controller).
#-----------------------------------------------------------------------------

	def get_temps(self, id=None, raw=False):
		str = self.get_status_report("temps", id, raw)
		ret = self.str2float(str)
		return ret

#-----------------------------------------------------------------------------
# Dome::get_status_report
# Description:
#	General status report parser function. For internal use.
#-----------------------------------------------------------------------------

	def get_status_report(self, mode, id=None, raw=False):
		if mode == "full":
			str = self.get_full_status_raw()
#			str = "Dome status: stopped Position: opened Motor: stopped Mode: failsafe on Output channels [1-16]: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, Input high voltage channels: 0, 0, 0, 0, 0, Input low voltage channels: 1, 1, 1, 1, 1, Dome position detectors: open: 0,1, close: 1,1, PSU DC OK: 0 UPS DC OK: 0 BAT DISCHG: 0 BAT FAIL: 0 motorCurrent: 0.2 A, limit: 3.50 A(enabled), abs max limit 7.0 A(enabled) ping watchdog enabled, timeout 6000, counter 289, ping reset watchdog enabled, timeout: 6000, counter: 289"
		elif mode == "brief":
			str = self.get_brief_status_raw()
#			str = "Dome status: stopped Position: opened Motor: stopped Mode: failsafe on"
		elif mode == "temps":
			str = self.get_temps_raw()
#			str = "Outside 12.3 C, Inside: 12.4 C, Motor: 12.5 C, Controller: 12.6 C"
		else:
			return None

		if str is None:
			return None

		if raw:
			return str
			
		if mode == "full":
			m = re.match(r"Dome status: (\w+) Position: (\w+) Motor: (\w+) Mode: ([\w\s]+) Output channels \[1-16\]: ([\w\s,]+) Input high voltage channels: ([\w\s,]+) Input low voltage channels: ([\w\s,]+) Dome position detectors: open: ([\w,]+) close: ([\w,]+) PSU DC OK: (\w+) UPS DC OK: (\w+) BAT DISCHG: (\w+) BAT FAIL: (\w+) motorCurrent: ([\w\.]+) A, limit: ([\w\.]+) A\(enabled\), abs max limit ([\w\.]+) A\(enabled\) ping watchdog (\w+), timeout (\w+), counter (\w+), ping reset watchdog (\w+), timeout: (\w+), counter: (\w+)", str)
			nid = 22
		elif mode == "brief":
			m = re.match(r"Dome status: (\w+) Position: (\w+) Motor: (\w+) Mode: ([\w\s]+)", str)
			nid = 4
		elif mode == "temps":
			m = re.match(r"Outside ([\w\.]+) C, Inside: ([\w\.]+) C, Motor: ([\w\.]+) C, Controller: ([\w\.]+) C", str)
			nid = 4
			
		if not m:
			return None
		retlist = [m.group(x) for x in range(1,nid+1)]

		if id is None:
			return retlist

		if type(id) is int:
			try:
				ret = retlist[id]
			except:
				ret = None
		else:
			try:
				ret = [retlist[x] for x in id]
			except:
				ret = None

		return ret

#-----------------------------------------------------------------------------
# Dome::get_channels
# Descrpiton:
#	Channel status parser function. For internal use.
#-----------------------------------------------------------------------------

	def get_channels(self, chid, channel=None):
		str = self.get_full_status(chid)
		if str  is None:
			return None
		strlist = str.rstrip(',').split(', ')
		chlist = [int(x) for x in strlist]
		if channel is None:
			return chlist
		try:
			ret = chlist[channel-1]
		except:
			ret = None
		return ret

#-----------------------------------------------------------------------------

#=============================================================================
# Low level functions for communication with the dome electronics tcp
# interface
#=============================================================================

#-----------------------------------------------------------------------------
# Dome::get_status_raw
#-----------------------------------------------------------------------------

	def get_full_status_raw(self):
		rcv = self.command_read('status')
		return rcv

#-----------------------------------------------------------------------------
# Dome::get_brief_status_raw
#-----------------------------------------------------------------------------

	def get_brief_status_raw(self):
		rcv = self.command_read('s')
		return rcv

#-----------------------------------------------------------------------------
# Dome::get_temps_raw
#-----------------------------------------------------------------------------

	def get_temps_raw(self):
		rcv = self.command_read('temps')
		return rcv

#-----------------------------------------------------------------------------
# Dome::send_open
#-----------------------------------------------------------------------------

	def send_open(self):
		ret = self.command_read('open')
		return ret

#-----------------------------------------------------------------------------
# Dome::send_close
#-----------------------------------------------------------------------------

	def send_close(self):
		ret = self.command_read('close')
		return ret

#-----------------------------------------------------------------------------
# Dome::stop
#-----------------------------------------------------------------------------

	def send_stop(self):
		ret = self.command_read('stop')
		return ret

#-----------------------------------------------------------------------------
# Dome::set_relay
#-----------------------------------------------------------------------------

	def set_relay(self, channel, state):
		if channel == 'all':
			cmd = 'relayAll %d' % (channel, state)
		else:
			cmd = 'relay %d %d' % (channel, state)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Dome::reset
#-----------------------------------------------------------------------------

	def reset(self):
		rcv = self.commad_read('reset')
		return rcv

#-----------------------------------------------------------------------------
# Dome::set_reset_timeout
#-----------------------------------------------------------------------------

	def set_reset_timeout(self, timeout):
		cmd = 'setResetTimeout %d' % (timeout,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Dome::set_ping_timeout
#-----------------------------------------------------------------------------

	def set_ping_timeout(self, timeout):
		cmd = 'setPingTimeout %d' % (timeout,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Dome::set_reset_watchdog
#-----------------------------------------------------------------------------

	def set_reset_watchdog(self, on):
		cmd = 'setResetWatchdog %d' % (on,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Dome::set_ping_watchdog
#-----------------------------------------------------------------------------

	def set_ping_watchdog(self, on):
		cmd = 'setPingWatchdog %d' % (on,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------

#=============================================================================
# Utility functions
#=============================================================================

#-----------------------------------------------------------------------------
# Dome::str2int
#-----------------------------------------------------------------------------

	def str2int(self, str):
		if type(str) is list or type(str) is tuple:
			try:
				ret = [int(x) for x in str]
			except:
				ret = None
		else:
			try:
				ret = int(str)
			except:
				ret = None
		return ret

#-----------------------------------------------------------------------------
# Dome::str2float
#-----------------------------------------------------------------------------

	def str2float(self, str):
		if type(str) is list or type(str) is tuple:
			try:
				ret = [float(x) for x in str]
			except:
				ret = None
		else:
			try:
				ret = float(str)
			except:
				ret = None
		return ret

#-----------------------------------------------------------------------------

#=============================================================================
