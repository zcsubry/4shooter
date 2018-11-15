# !/usr/bin/env python
#=============================================================================

import tcpdevice

import time
import re
from optparse import OptionParser


HOME_STATUS_FAILED	=	0
HOME_STATUS_OK		=	1
HOME_STATUS_SEARCH	=	2

MOVE_STATUS_FAILED	=	0
MOVE_STATUS_OK		=	1
MOVE_STATUS_MOVING	=	2

#=============================================================================
# Scope
#=============================================================================
#
# Class: Scope
#
# Class for controlling the scope. The class uses the TCPDevice class in
# order to connect and communicate with the Hydra telescope control.
#
# The functions are grouped with two main class:
#
# Interface commands:
#	These are high level functions and intended for the user to call from
#	the controller software during normal operation.
# Low-level commands:
#	These functions are for internal use and not supposed to call from
#	outside the class during normal operation.
#
# List of interface commands:
#	__init__(self):
#	connect(self):
#	home(self, wait=True):
#	park(self, wait=True):
#	move_coo(self, coo1, coo2, sys='equ2', wait=True):
#	get_coo(self, check_precision=True, coosys='equ2'):
#	set_coo(self, ra, dec, coosys='equ2'):
#	halt(self):
#	get_tracking(self):
#	set_tracking(self, on):
#	start_tracking(self):
#	stop_tracking(self):
#	get_tracking_rate(self):
#	set_tracking_rate(self, rate):
#	off(self):
#	on(self):
#	get_alt_limit(self):
#	set_alt_limit(self, min, max):
#	get_geocoo(self):
#	set_geocoo(self, long, lat):
#	get_datetime(self, sys='local'):
#	set_datetime(self, date, time, sys='local'):
#	get_timezone(self):
#	set_timezone(self, tz):
#
#=============================================================================

class Scope(tcpdevice.TCPDevice):

#-----------------------------------------------------------------------------
# Scope::__init__
# Description:
#	Class constructor function.
#-----------------------------------------------------------------------------

	def __init__(self):
		tcpdevice.TCPDevice.__init__(self)
		self.set_format(':%s#\n')
		self.status = {}
		self.status['home'] = 0
		self.status['move'] = 0

		self.timeout['default'] = 120
		self.timeout['home'] = 240
		self.timeout['move'] = 180

		return

#-----------------------------------------------------------------------------
# Scope::connect
#-----------------------------------------------------------------------------

	def connect(self):
		ret = tcpdevice.TCPDevice.connect(self)
		if not ret:
			return False
		self.get_coo(check_precision=True, coosys='altaz')
		return True

#-----------------------------------------------------------------------------

#=============================================================================
# Interface: Scope coordinates and movement
#
# High level commands to home and position the scope and manipulating the
# coordinates.
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::home
# Description:
#	Move the scope to the home position and start tracking. If $wait=True,
#	then the functions waits until the homing is finished or failed or
#	timeout occured.
# Return:
#	- True/False
#-----------------------------------------------------------------------------

	def home(self, wait=True):

		ret = self.seek_home()
		if not ret:
			return False

		if not wait:
			return True

		timeout = self.get_timeout('home');
		ret = tcpdevice.waitfor(self.get_home_status, '!=', HOME_STATUS_SEARCH,
			timeout)
		if not ret:
			return False

		ret = self.get_home_status()
		if ret == HOME_STATUS_OK:
			return True
		return False

#-----------------------------------------------------------------------------
# Scope::park
# Description:
#	Move the scope to park position and turn off tracking. The function does
#	not wait until the park position reached.
#-----------------------------------------------------------------------------

	def park(self, wait=True):
		ret = self.move_park()
		if not ret:
			return False
		
		if not wait:
			return True
			
		return True

#-----------------------------------------------------------------------------
# Scope::move_coo
# Synopsis:
#	move_coo coo1 coo2 sys wait
# Input:
#	- coo1 (%hms/%dms)
#		First coordinate (RA, HA or azimuth) in hh:mm:ss.s or dd:mm:ss.s format.
#	- coo2 (%hms/%dms)
#		Second coordinate (Dec or altitude) in dd:mm:ss.s format.
#	- sys (equ1|equ2|altaz):
#		Coordinate system. Default: equ2
#	- wait (0|1)
#		Wait flag. Default: True
# Description:
#	Move the telescope to the target coordinate. Wait until the scope
#	reaches the coordinate (or fails) if $wait = True.
# Return:
#	True/False
# Note:
#	Only the Equatorial II coordinate system is fully implemented.
#-----------------------------------------------------------------------------

	def move_coo(self, coo1, coo2, sys='equ2', wait=True):
		coo1 = self.float2dms(coo1)
		coo2 = self.float2dms(coo2)
		self.set_target_ra(coo1)
		self.set_target_dec(coo2)
		ret = self.move_target(sys)
		if not ret:
			return False
		
		if not wait:
			return True
			
		timeout = self.get_timeout('move_coo');
		ret = tcpdevice.waitfor(self.get_move_status, '!=', MOVE_STATUS_MOVING,
			timeout)
		if not ret:
			return False

		ret = self.get_move_status()
		if ret == MOVE_STATUS_OK:
			return True
		
		return False

#-----------------------------------------------------------------------------
# Scope::get_coo
# Synopsis:
#	get_coo check_precision coosys
# Input:
#	- check_precision (0|1):
#		If True, than check if the coordinate display is set to high
#		precision.
#	- coosys (equ1|equ2|altaz)
#		Coordinate system.
# Description:
#	Query the current scope coordinates.
# Return:
#	Tuple of containing coo2 and coo2 in hh:mm.ss or dd:mm:ss format.
#-----------------------------------------------------------------------------

	def get_coo(self, check_precision=True, coosys='equ2'):
		if coosys == 'altaz':
			get_coo1 = self.get_az
			get_coo2 = self.get_alt
		else:
			get_coo1 = self.get_ra
			get_coo2 = self.get_dec

		coo1 = get_coo1()
		coo2 = get_coo2()

		if check_precision and coo1 == '00:00:00' and coo2 == '00:00:00':
			self.toggle_precision()
			coo1 = get_coo1()
			coo2 = get_coo2()

		return coo1, coo2

#-----------------------------------------------------------------------------
# Scope::set_coo
# Synopsis:
#	set_coo coo1 coo2
# Input:
#	- coo1 (%hms/%dms)
#		First coordinate (RA, HA or azimuth) in hh:mm:ss.s or dd:mm:ss.s format.
#	- coo2 (%hms/%dms)
#		Second coordinate (Dec or altitude) in dd:mm:ss.s format.
#	- sys (equ1|equ2|altaz):
#		Coordinate system. Default: equ2
# Description:
#	Overwrites the current coordinates with $coo1 and $coo2.
#-----------------------------------------------------------------------------

	def set_coo(self, coo1, coo2, coosys='equ2'):
		coo1 = self.float2dms(coo1)
		coo2 = self.float2dms(coo2)
		self.set_target_ra(coo1)
		self.set_target_dec(coo2)
		self.sync_target()
		return

#-----------------------------------------------------------------------------
# Scope::halt
# Description:
#	Stop the telescope movement.
#-----------------------------------------------------------------------------

	def halt(self):
		return self.stop_move()

#-----------------------------------------------------------------------------

#=============================================================================
# Interface: Scope status, tracking
#
# High level commands to query the telescope status and tracking.
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_tracking
# Description:
#	Query if the tracking is on.
# Return:
#	True/False
#-----------------------------------------------------------------------------

	def get_tracking(self):
		mount, tracking, alignment = self.get_alignment_status()
		if tracking == 'T':
			return True
		return False

#-----------------------------------------------------------------------------
# Scope::set_tracking
# Synopsis:
#	set_tracking track
# Input:
#	- track (0|1):
# Description:
#	Start or stop the telescope tracking.
#-----------------------------------------------------------------------------

	def set_tracking(self, on):
		ison = self.get_tracking()
		if ison == on:
			return
		if on:
			rcv = self.command_read('ST60.1')
		else:
			rcv = self.command_read('ST0.0')
		return rcv

#-----------------------------------------------------------------------------
# Scope::start_tracking
# Description:
#	Start tracking.
#-----------------------------------------------------------------------------

	def start_tracking(self):
		return self.set_tracking(True)

#-----------------------------------------------------------------------------
# Scope::stop_tracking
# Description:
#	Stop tracking.
#-----------------------------------------------------------------------------

	def stop_tracking(self):
		return self.set_tracking(False)

#-----------------------------------------------------------------------------
# Scope::get_tracking_rate
# Description:
#	Query the currently set tracking rate.
# Return:
#	Tracking rate in Herz (60.0Hz = 1 rev in 24 hours).
#-----------------------------------------------------------------------------

	def get_tracking_rate(self):
		return self.command_read('GT')

#-----------------------------------------------------------------------------
# Scope::set_tracking_rate
# Synopsis:
#	set_tracking_rate rate
# Input:
#	- rate (%f): Tracking rat in Herz (60.0Hz = 1 rev in 24 hours)
#-----------------------------------------------------------------------------

	def set_tracking_rate(self, rate):
		cmd = 'ST%s' % rate 
		return self.command_read(cmd)

#-----------------------------------------------------------------------------
# Scope::set_tracking_rate
#-----------------------------------------------------------------------------
#
#	def set_tracking_rate(self, rate):
#		if rate == 'l' or rate == 'lunar':
#			cmd = 'TL'
#		elif rate == 'd' or rate == 'default':
#			cmd = 'TQ'
#		elif rate == 's' or rate == 'solar':
#			cmd = 'TS'
#		else:
#			return
#		rcv = self.command_read(cmd)
#		return rcv
#
#-----------------------------------------------------------------------------

#=============================================================================
# Interface: Initialization and setup
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::off
# Description:
#	Power down the scope or send it to sleep mode.
#-----------------------------------------------------------------------------

	def off(self):
		return self.sleep()

#-----------------------------------------------------------------------------
# Scope::on
# Description
#	Power or wake up the scope.
#-----------------------------------------------------------------------------

	def on(self):
		return self.wakeup()

#-----------------------------------------------------------------------------
# Scope::get_alt_limit
# Description:
#	Query the scope altitude limits.
# Return:
#	min, max: Minimum altitude, maximum altitude
#-----------------------------------------------------------------------------

	def get_alt_limit(self):
		min = self.get_low_limit()
		max = self.get_high_limit()
		return min, max

#-----------------------------------------------------------------------------
# Scope::set_alt_limit
# Synopsis:
#	set_alt_limit min max
# Input:
#	- min ($f):
#		Minimum altitude [deg]
#	- max ($f):
#		Maximum altitude [deg]
# Description:
#	Set the scope altitude limits (min and max)
#-----------------------------------------------------------------------------

	def set_alt_limit(self, min, max):
		self.set_low_limit(min)
		self.set_high_limit(max)
		return self.get_alt_limit()

#-----------------------------------------------------------------------------

#=============================================================================
# Interface: Site coordinates and date-time
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_geocoo
# Description:
#	Return the geographical coordinates of the telescope.
# Return:
#	List of longitude and latiuted.
#-----------------------------------------------------------------------------

	def get_geocoo(self):
		long = self.get_longitude()
		lat = self.get_latitude()
		return long, lat

#-----------------------------------------------------------------------------
# Scope::set_geocoo
# Synopsis:
#	Scope::set_coo long lat
# Input:
#	-	long (%dd:mm:ss.ss):
#			Geographical longitude.
#	-	lat (%dd:mm:ss.ss):
#			Geographical latitude
# Description:
#	Sets the geographical coordinates of the telescope.
#-----------------------------------------------------------------------------

	def set_geocoo(self, long, lat):
		self.set_longitude(long)
		self.set_latitude(lat)
		return self.get_geocoo()

#-----------------------------------------------------------------------------
# Scope::get_datetime
# Synopsis:
#	Scope::get_datetime [sys]
# Input:
#	- sys (local|utc|sidereal):
#		Time system (default is local)
# Description:
#	Returns the current date and time according to the telescope clock.
#	Optionally the time system can be specified.
# Return:
#	String of date and time
# Note:
#	Only local time is implemented.
#-----------------------------------------------------------------------------

	def get_datetime(self, sys='local'):
		date = self.get_local_date()
		time = sefl.get_local_time()
		return date, time

#-----------------------------------------------------------------------------
# Scope::set_datetime
# Synopsis:
#	Scope::set_datetime datetime [sys]
# Input:
#	- datetime (yyyy-mm-dd hh:mm:ss.ss):
#		String of date and time
#	- sys (local|utc|sidereal):
#		Time system (default is local)
# Description:
#	Sets the current time of the telescope clock.  Optionally the time
#	system can be specified.
#-----------------------------------------------------------------------------

	def set_datetime(self, date, time, sys='local'):
		self.set_local_date(date)
		self.set_local_time(time)
		return self.get_datetime(sys)

#-----------------------------------------------------------------------------
# Scope::get_timezone
# Description:
#	Query the current time zone.
# Return:
#	Time difference from Greenwich [hours].
#-----------------------------------------------------------------------------

	def get_timezone(self):
		tz = self.get_utc_offset()
		return tz

#-----------------------------------------------------------------------------
# Scope::set_timezone
# Synopsis:
#	Scope::set_timezone tz
# Input:
#	- tz (%f):
#		Time difference from Greenwich in hours.
# Synopsis:
#	Sets the telescope time zone.
#-----------------------------------------------------------------------------

	def set_timezone(self, tz):
		self.set_utc_offset(tz)
		return self.get_utc_offset()

#-----------------------------------------------------------------------------

#=============================================================================
# LOW-LEWEL MEADE PROTOCOL COMMANDS
#=============================================================================

#=============================================================================
# Low level: Site coordinates and date-time
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_longitude
# Description:
#	Query the site longitude.
# Return:
#	Site longitude [deg]
#-----------------------------------------------------------------------------

	def get_longitude(self):
		rcv = self.command_read('Gg')
		long = "%s:%s:%s" % self.parse_coo(rcv)
		return long

#-----------------------------------------------------------------------------
# Scope::get_latitude
# Description:
#	Query the site latitude.
# Return:
#	Site latitude [deg]
#-----------------------------------------------------------------------------

	def get_latitude(self):
		rcv = self.command_read('Gt')
		lat = "%s:%s:%s" % self.parse_coo(rcv)
		return lat

#-----------------------------------------------------------------------------
# Scope::set_longitude
# Synopsis:
#	set_longitude long
# Input:
#	- longitude (%f):
#		Site longitude [deg]
# Set the site longitude.
#-----------------------------------------------------------------------------

	def set_longitude(self, long):
		cmd = "Sg%s*%s*%s" % tuple(long.split(':'))
		rcv = self.command_read(cmd) 
		return rcv

#-----------------------------------------------------------------------------
# Scope::set_latitude
# Synopsis:
#	set_latitude long
# Input:
#	- latitude (%f):
#		Site latitude [deg]
# Set the site latitude.
#-----------------------------------------------------------------------------

	def set_latitude(self, lat):
		cmd = "St%s*%s*%s" % tuple(long.split(':'))
		rcv = self.command_read(cmd) 
		return rcv

#-----------------------------------------------------------------------------
# Scope::get_local_date
# Description:
#	Returns the current local date according to the telescope clock.
# Return:
#	Local date (yyyy-mm-dd)
#-----------------------------------------------------------------------------

	def get_local_date(self):
		rcv = self.command_read('GC')
		y, m, d = self.parse_date(rcv)
		date = "20%s-%s-%s" % (y, m, d)
		return date

#-----------------------------------------------------------------------------
# Scope::get_local_time
# Description:
#	Returns the current local time according to the telescope clock.
# Return:
#	Local time (hh:mm:ss)
#-----------------------------------------------------------------------------

	def get_local_time(self):
		rcv = self.command_read('GL')
		h, m, s = self.parse_time(rcv)
		time = "%s:%s:%s" % (h, m, s)
		return time

#-----------------------------------------------------------------------------
# Scope::set_local_date
# Synopsis:
#	Scope::set_local_date date
# Input:
#	- date (yyyy-mm-dd):
#		String of date.
# Description:
#	Sets the current local date of the telescope clock.
#-----------------------------------------------------------------------------

	def set_local_date(self, date):
		y, m, d = date.split('-')
		y = y[-2:]
		cmd = "SC%s/%s/%s" % (m, d, y)
		return

#-----------------------------------------------------------------------------
# Scope::set_local_time
# Synopsis:
#	Scope::set_local_time time
# Input:
#	- time (hh:mm:ss):
#		String of time.
# Description:
#	Sets the current local time of the telescope clock.
#-----------------------------------------------------------------------------

	def set_local_time(self, time):
		h, m, s = date.split(':')
		cmd = "SL%s:%s:%s" % (h, m, s)
		return

#-----------------------------------------------------------------------------
# Scope::get_sidereal_time
# Description:
#	Returns the current sidereal time according to the telescope clock.
# Return:
#	Sidereal time(hh:mm:ss)
#-----------------------------------------------------------------------------

	def get_sidereal_time(self):
		rcv = self.command.read('GS')
		h, m, s = self.parse_time(rcv)
		time = "%s:%s:%s" % (h, m, s)
		return rcv

#-----------------------------------------------------------------------------
# Scope::get_utc_offset
# Description:
#	Query the UTC offset of the scope clock.
# Return:
#	UTC offset [hour]
#-----------------------------------------------------------------------------

	def get_utc_offset(self):
		rcv = self.command_read('GG')
		return rcv

#-----------------------------------------------------------------------------
# Scope::set_utc_offset
#  Synopsis:
#	set_utc_offset offset
# Input:
#	- offset (%f):
#		Offset from UTC [hour]
# Description:
#	Set the UTC offset of the scope clock.
#-----------------------------------------------------------------------------

	def set_utc_offset(self, offset):
		if offset > 0:
			cmd = 'SG+%4.1f' % (offset,)
		else:
			cmd = 'SG%4.1f' % (offset,) 
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Scope::toggle_time_format
# Description:
#	Toggle between low and high precision display.
#-----------------------------------------------------------------------------

	def toggle_time_format(self):
		rcv = self.command_read('H')
		return 

#-----------------------------------------------------------------------------

#=============================================================================
# Telescope coordinates
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_ra
# Description:
#	Query current RA.
# Return:
#	RA in hh:mm:ss format.
#-----------------------------------------------------------------------------

	def get_ra(self):
		rcv = self.command_read('GR')
		ra = "%s:%s:%s" % self.parse_coo(rcv)
		return ra

#-----------------------------------------------------------------------------
# Scope::get_dec
# Description:
#	Query current declination
# Return:
#	Declination in dd:mm:ss format.
#-----------------------------------------------------------------------------

	def get_dec(self):
		rcv = self.command_read('GD')
		dec = "%s:%s:%s" % self.parse_coo(rcv)
		return dec

#-----------------------------------------------------------------------------
# Scope::get_az
# Description:
#	Query current azimuth
# Return:
#	Azimuth in dd:mm:ss format.
#-----------------------------------------------------------------------------

	def get_az(self):
		rcv = self.command_read('GZ')
		az = "%s:%s:%s" % self.parse_coo(rcv)
		return az

#-----------------------------------------------------------------------------
# Scope::get_alt
# Description:
#	Query current altitude
# Return:
#	Altitude in dd:mm:ss format.
#-----------------------------------------------------------------------------

	def get_alt(self):
		rcv = self.command_read('GA')
		alt = "%s:%s:%s" % self.parse_coo(rcv)
		return alt

#-----------------------------------------------------------------------------

#=============================================================================
# Target coordinate commands
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_target_ra
#-----------------------------------------------------------------------------

	def get_target_ra(self):
		rcv = self.command_read('Gr')
		dec = "%s:%s:%s" % self.parse_coo(rcv)
		return dec

#-----------------------------------------------------------------------------
# Scope::get_target_dec
#-----------------------------------------------------------------------------

	def get_target_dec(self):
		rcv = self.command_read('Gd')
		dec = "%s:%s:%s" % self.parse_coo(rcv)
		return dec

#-----------------------------------------------------------------------------
# Scope::get_target_coo
#-----------------------------------------------------------------------------

	def get_target_coo(self, sys='equ2'):
		if sys == 'altaz':
			coo1 = self.get_target_az()
			coo2 = self.get_target_alt()
		elif sys == 'equ1':
			coo1 = self.get_target_ha()
			coo2 = self.get_target_dec()
		else:
			coo1 = self.get_target_ra()
			coo2 = self.get_target_dec()
		return coo1, coo2
		
#-----------------------------------------------------------------------------
# Scope::set_target_ra
#-----------------------------------------------------------------------------

	def set_target_ra(self, ra):
		ra = self.format_coo(ra, 'h')
		cmd = "Sr%s" % (ra,)
		rcv = self.command_read(cmd)
		return rcv 

#-----------------------------------------------------------------------------
# Scope::set_target_dec
#-----------------------------------------------------------------------------

	def set_target_dec(self, dec):
		dec = self.format_coo(dec, 'd')
		cmd = "Sd%s" % (dec,)
		rcv = self.command_read(cmd)
		return rcv 

#-----------------------------------------------------------------------------
# Scope::set_target_ha
#-----------------------------------------------------------------------------

	def set_target_ha(self, ha):
		pass


#-----------------------------------------------------------------------------
# Scope::set_target_az
#-----------------------------------------------------------------------------

	def set_target_az(self, az):
		alt = self.format_coo(az)
		cmd = "Sz%s" % (az)
		rcv = self.command_read(cmd)
		return rcv 

#-----------------------------------------------------------------------------
# Scope::set_target_alt
#-----------------------------------------------------------------------------

	def set_target_alt(self, alt):
		alt = self.format_coo(alt)
		cmd = "Sa%s" % (alt,)
		rcv = self.command_read(cmd)
		return rcv 

#-----------------------------------------------------------------------------
# Scope::get_target
#-----------------------------------------------------------------------------

	def set_target_coo(self, coo1, coo2,  sys='equ2'):
		if sys == 'altaz':
			r1 = self.set_target_az(coo1)
			r2 = self.set_target_alt(coo2)
		elif sys == 'equ1':
			r1 = self.set_target_ha(coo1)
			r2 = self.set_target_dec(coo2)
		else:
			r1 = self.set_target_ra(coo1)
			r2 = self.set_target_dec(coo2)
		return r1, r2
		
#-----------------------------------------------------------------------------
# Scope::sync_target
# Description:
#	Set the scope current coordinates to the target coordinates.
#-----------------------------------------------------------------------------

	def sync_target(self):
		rcv = self.command_read('CM')
		return rcv

#-----------------------------------------------------------------------------


#=============================================================================
# Scope movement
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::move_target
# Descirption:
#	Move the scope to the target coordinates. (Target coordinates are to be
#	set with 'set_target' functions).
#-----------------------------------------------------------------------------

	def move_target(self, sys='equ2'):

		if sys == 'altaz':
			cmd = 'MA'
		elif sys == 'equ1':
			cmd = ''
		else:
			cmd = 'MS'

		try:
			rcv = self.command_read(cmd, sleep=0.6)
		except:
			return False

		if int(rcv[0]) == 0:
			return True

		return False

#-----------------------------------------------------------------------------
# Scope::move_dir
# Synopsis:
#	move_dir dir
# Input:
#	- dir (n|e|s|w): Directions (north, east, south, west)
# Description:
#	Start moving the telescope to the selected direction.
#-----------------------------------------------------------------------------

	def move_dir(self, dir=None):
		if dir in ('n', 'e', 's', 'w'):
			cmd = "M%s" % (dir,)
		else:
			return
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Scope::stop_move
# Synopsis:
#	stop_move dir
# Input:
#	- dir (n|e|s|w): Directions (north, east, south, west)
# Description:
#	Stop the telescope moving to the selected direction. If no direction is
#	selected, that every movement stops.
#-----------------------------------------------------------------------------

	def stop_move(self, dir=None):
		if dir is None:
			cmd = 'Q'
		elif dir in ('n', 'e', 's', 'w'):
			cmd = "Q%s" % (dir,)
		else:
			return
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------

#=============================================================================
# Home position
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::seek_home
# Description:
#	Send a 'home' command to the scope and returns immediately.
#-----------------------------------------------------------------------------

	def seek_home(self):
		try:
			self.command_read('hF')
		except:
			return False
		return True

#-----------------------------------------------------------------------------
# Scope::get_home_status
# Description:
#	Query the status of the current homing process.
# Return:
#	- 	0: Home search failed
#	- 	1: Home found
#	-	2: Home search in progress
#-----------------------------------------------------------------------------

	def get_home_status(self):
		rcv = self.command_read('h?')
		if not rcv:
			return None
		return int(rcv[0])

#-----------------------------------------------------------------------------
# Scope::get_move_status
# Description:
#	Return the status of the current moving process.
# Return:
#	- 	0: Move failed
#	- 	1: Move succeeded
#	-	2: Move in progress
#-----------------------------------------------------------------------------

	def get_move_status(self):
		ret = self.get_home_status()
		if ret == HOME_STATUS_FAILED:
			return MOVE_STATUS_MOVING
		return MOVE_STATUS_OK

#-----------------------------------------------------------------------------
# Scope::set_park
# Description:
#	Set the current position of the scope as 'park' position.
#-----------------------------------------------------------------------------

	def set_park(self):
		rcv = self.command_read('hS')
		return

#-----------------------------------------------------------------------------
# Scope::move_park
# Description:
#	Sends a park comband to the scope and returns immediately.
#-----------------------------------------------------------------------------

	def move_park(self):
		try:
			self.command_read('hP')
		except:
			return False
		return True

#-----------------------------------------------------------------------------
# Scope::sleep
# Description:
#	Power down the scope or send it to sleep mode.
#-----------------------------------------------------------------------------

	def sleep(self):
		rcv = self.command_read('hN')
		return

#-----------------------------------------------------------------------------
# Scope::wakeup
# Description:
#	Power or wake up the telescope.
#-----------------------------------------------------------------------------

	def wakeup(self):
		rcv = self.command_read('hW')
		return

#-----------------------------------------------------------------------------

#=============================================================================
# Telescope status
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_firmware
#-----------------------------------------------------------------------------

	def get_telescope_firmware(self):
		rcv = self.command_read("GVN")
		return rcv

#-----------------------------------------------------------------------------
# Scope::get_telescope_product
#-----------------------------------------------------------------------------

	def get_telescope_product(self):
		rcv = self.command_read("GVP")
		return rcv

#-----------------------------------------------------------------------------
# Scope::get_alignment_status
# Description:
#	Query the scope alignment.
# Return:
#	List of mount, tracking, alignment
#	- mount: A - AzEl mounted, P - equatorially mounted, G - german mounted
#	- tracking: T - tracking, N - not tracking
#	- alignment: 0 - needs alignment, 1 - one star alignment, 2 - two star alignment
#-----------------------------------------------------------------------------

	def get_alignment_status(self):
		rcv = self.command_read("GW")
		if not rcv:
			return None, None, None
		mount, tracking, alignment = tuple(list(rcv))
		return mount, tracking, alignment

#-----------------------------------------------------------------------------
# Scope::get_slew_rate
#-----------------------------------------------------------------------------

	def get_slew_rate(self):
		pass

#-----------------------------------------------------------------------------
# Scope::set_slew_rate
# Synopsis:
#	set_slew_rate rate, ra, dec
# Input:
#	- rate (c|g|f|m):
#		Slew rates:
#			- c: centerinng rate (16x sidereal)
#			- g: guiding rate (2x sidereal)
#			- f: find rate (1 degree per second)
#			- m: move rate (4 degree per second)
#	- ra (0|1)
#		Apply the slew rate to the RA axis.
#	- dec (0|1)
#		Apply the slew rate to the Dec axis.
# Description:
#	Set the slew rate of the selected axis.
#-----------------------------------------------------------------------------

	def set_slew_rate(self, rate=None, ra=None, dec=None):
		if rate:
			if rate == 'center' or rate == 'c':
				cmd = 'RC'
			elif rate == 'guide' or rate == 'g':
				cmd = 'RG'
			elif rate == 'find' or rate == 'f':
				cmd = 'RM'
			elif rate == 'max' or rate == 'm':
				cmd = 'RS'
			else:
				return
			rcv = self.command_read(cmd)

		if ra:
			cmd = 'RA%s' % (ra,)
			rcv = self.command_read(cmd)

		if dec:
			cmd = 'RE%s' % (ra,)
			rcv = self.command_read(cmd)

		return

#-----------------------------------------------------------------------------
# Scope::set_max_slew_rate
#  Synopsis:
#	set_max_slew_rate N
# Input:
#	- N (%d):
#		Slew rate (2..8)
# Description:
#	Set the maximum  slew rate to N degrees per second).
#-----------------------------------------------------------------------------

	def set_max_slew_rate(self, N):
		cmd = 'SW%d' % (N,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------


#=============================================================================
# Telescope setup
#=============================================================================

#-----------------------------------------------------------------------------
# Scope::get_high_limit
#-----------------------------------------------------------------------------

	def get_high_limit(self):
		rcv = self.command_read("Gh")
		return rcv

#-----------------------------------------------------------------------------
# Scope::get_low_limit
#-----------------------------------------------------------------------------

	def get_low_limit(self):
		rcv = self.command_read("Go")
		return rcv

#-----------------------------------------------------------------------------
# Scope::set_high_limit
#-----------------------------------------------------------------------------

	def set_high_limit(self, limit):
		cmd = 'Sh%d' % (limit,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Scope::set_low_limit
#-----------------------------------------------------------------------------

	def set_low_limit(self, limit):
		cmd = 'So%d' % (limit,)
		rcv = self.command_read(cmd)
		return rcv

#-----------------------------------------------------------------------------
# Scope::toggle_precision
#-----------------------------------------------------------------------------

	def toggle_precision(self):
		return self.command_read('U')

#-----------------------------------------------------------------------------

#=============================================================================
# Parse and format time and coordinate values and convert them between
# hh:mm:ss and hydra formats.
#=============================================================================

#-----------------------------------------------------------------------------
# parse_coo
#-----------------------------------------------------------------------------

	def parse_coo(self, coo):
		try:
			d, m, s =  tuple(re.split("\*|:", coo))
		except:
			d, m, s = ('00', '00', '00')
		if '#' in d:
			tmp = d.split('#')[1]
			d = tmp
		return d, m, s

#-----------------------------------------------------------------------------
# parse_time
#-----------------------------------------------------------------------------

	def parse_time(self, time):
		h, m, s = time.split(":")
		return h, m, s

#-----------------------------------------------------------------------------
# parse_date
#-----------------------------------------------------------------------------

	def parse_date(self, date):
		m, d, y = date.split("/")
		return y, m, d

#-----------------------------------------------------------------------------
# format_coo
#-----------------------------------------------------------------------------

	def format_coo(self, coo, unit='d'):
		d, m, s =  coo.split(':')
		str =  "%s:%s:%s" % (d, m, s)

		if d[0] == '-':
			sig = '-'
		else:
			sig = '+'
		
		id = abs(int(d))	
		if id < 10:
			d = "0%d" % (id,)
		else:
			d = "%d" % (id,)
			
		if unit == 'd':
			str =  "%s%s*%s:%s" % (sig, d, m, s)
		else:
			str =  "%s:%s:%s" % (d, m, s)

		return str

#-----------------------------------------------------------------------------
# format_time
#-----------------------------------------------------------------------------

	def format_time(self, time):
		h, m, s =  coo.split(':')
		str =  "%s:%s:%s" % (h, m, s)
		return str

#-----------------------------------------------------------------------------
# format_date
#-----------------------------------------------------------------------------

	def format_date(self, date):
		y, m, d =  coo.split('-')
		y = y[-2:]
		str =  "%s/%s/%s" % (m, d, y)
		return str

#-----------------------------------------------------------------------------
# float2dms
# Description:
#	Convert a float or integer coordinate to dd:mm:ss format.
#-----------------------------------------------------------------------------

	def float2dms(self, dd):
		if type(dd) is str:
			return dd
		deg = int(dd)
		minsec = divmod((dd-deg)*60.0, 60)[-1]
		min = int(minsec)
		secs = divmod((minsec-min)*60.0, 60)[-1]
		sec = int(secs)
		dms = "%02d:%02d:%02d" % (deg, min, sec)
		return dms

#-----------------------------------------------------------------------------

#=============================================================================
# Main program (for testing and debugging)
#=============================================================================

# read_command_line
#-----------------------------------------------------------------------------

def read_command_line():

	parser = OptionParser(usage='%prog [--options]')
	
	parser.add_option('--host', dest='host', default='192.168.1.211',
			action='store', type='str')
	parser.add_option('--port', dest='port', default=10001,
			action='store', type='int')
	parser.add_option('--msg', dest='msg', default=None,
			action='store', type='str')
	parser.add_option('--cmd', dest='cmd', default=None,
			action='store', type='str')

	try:
		options, args = parser.parse_args()
	except Exception, error:
		parser.print_help()
		print error
		exit(1)

	return options

#-----------------------------------------------------------------------------

if __name__=='__main__' :

	options = read_command_line()

	# Connect to device
	dev = Scope(host=options.host, port=options.port)
	if not dev.connect():
		print "Failed to connect to device!"
		exit(0)

	if options.msg is not None:
		dev.write(options.msg)
		time.sleep(0.1)
		print dev.read()

	if options.cmd is not None:
		print dev.execute(options.cmd)

	# Disconnect from device
	dev.disconnect()

#=============================================================================
