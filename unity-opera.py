#!/usr/bin/env python
########################################################
# Unity Opera
#
# Author:      Kyle Baker (kyleabaker.com)
#              Sebastian Wagner (github.com/sebix)
# Description: Provides several features for Unity users
#              who also use Opera or Opera Next that are
#              not available by default.
# Version:     2011-08-01
# Help:        unity-opera.py --help
########################################################

from gi.repository import Unity, Gio, GObject, Dbusmenu
from cStringIO import StringIO
import sys, os, commands, subprocess, re
import argparse

loop = GObject.MainLoop()

# Initialization of global variables
home = os.getenv("HOME")
current_tabs = 0
current_speeddial = ""
tab_count_changed = False
is_first_check = True

# Set version of Opera here from command args or assume opera (opera, opera-next)
#         format: python unity-opera.py (opera | opera-next) (-lscup -v | -q)
parser = argparse.ArgumentParser(
	description='''Unity-Opera\n
Unity-Opera integrates the Opera-Browser into your Unity-Desktop Environment (Ubuntu GNU/Linux 11.04 Maverick Meerkat)''',
	formatter_class=argparse.RawDescriptionHelpFormatter,
	epilog='''
Notes:\n\
	* Progress bar for downloads is not functional at this time and may not be possible.\n

Example usage:\n\
	Use all available features\n\
		$ python unity-opera.py\n\
	Count tabs and use urgency notification\n\
		$ python unity-opera.py opera -cu\n\
	Use Opera Next and only Quicklist with Speed Dial entries\n\
		$ python unity-opera.py opera-next -ls''')
parser.add_argument(
	'-n', '--next', action='store_const',
	dest='program', const='opera-next', default='opera',
	help='Use Opera-Next instead of Opera')
parser.add_argument(
	'-l', '--quicklist', action='store_true',
	help='Use Opera-Next instead of Opera')
parser.add_argument(
	'-s', '--speeddial', action='store_true',
	help='Enable Speed Dial entries in quicklist')
parser.add_argument(
	'-c', '--tabcount', action='store_true',
	help='Enable tab count')
parser.add_argument(
	'-u', '--urgency', action='store_true',
	help='Enable urgency notification')
parser.add_argument(
	'-p', '--progress-bar', action='store_true',
	help='Enable progress bar for downloads')
parser.add_argument(
	'-v', '--verbose', action='store_const',
	dest='log_level', const=0, default=1,
	help='Enable LogLevel verbose')
parser.add_argument(
	'-q', '--quiet', action='store_const',
	dest='log_level', const=2, default=1,
	help='Enable LogLevel quiet')

args = parser.parse_args()

if (len(sys.argv) == 1):
	# Use all features
	args.quicklist = True
	args.speeddial = True
	args.tabcount = True
	args.urgency = True
	args.progressbar = True

# Pretend to be opera
launcher = Unity.LauncherEntry.get_for_desktop_id (args.program + "-browser.desktop")


########################################################
# log(message, priority)
#
# Author: Sebastian Wagner (https://github.com/sebix)
# Description: Send output, depending on log level
# Log Levels:
# * 0 Verbose
# * 1 normal
# * 2 Quiet
########################################################
def log(message, priority = 1):
#	global args;
	if priority >= args.log_level:
		print message
		return True
	else:
		return False


########################################################
# is_opera_running()
#
# Description: Returns boolean True if Opera is running
########################################################
def is_opera_running():
	output = commands.getoutput("ps -A | grep '" + args.program + "' | awk '{print $4}'").split('\n')
	for i in output:
		if i == args.program:
			return True
	return False


########################################################
# menu_open_new_tab(a, b)
# menu_open_new_private_tab(a, b)
# menu_open_new_window(a, b)
# menu_open_speeddial_item(a, b, url)
# update_quicklist()
#
# Description: List of functions for quicklist menu
########################################################
def menu_open_new_tab(a, b):
	os.popen3(args.program + " -newtab")
def menu_open_new_private_tab(a, b):
	os.popen3(args.program + " -newprivatetab")
def menu_open_new_window(a, b):
	os.popen3(args.program + " -newwindow")
def menu_open_mail(a, b):
	os.popen3(args.program + " -mail")
	#TODO: Fix this command so it actually opens M2
def menu_open_speeddial_item(a, b, url):
	os.popen3(args.program + " " + url)
def update_quicklist():
	# Set quicklist menu items from speeddial
	global current_speeddial, args
	title = ""
	url = ""
	
	# Make sure the speed dial file exists before attempting to read it
	if not os.path.isfile(home + "/." + args.program + "/speeddial.ini"):
		log("Error: Unable to open " + home + "/." + args.program + "/speeddial.ini", 2)
		exit()
	else:
		if args.speeddial:
			try:
				file = open(home + "/." + args.program + "/speeddial.ini")
				temp = file.read()
				if temp == current_speeddial:
					return True
				else:
					current_speeddial = temp
					log("Updating Quicklist with Speed Dial entries", 1)
				file.close()
			except IOError:
				pass
		
		#TODO: Clear items previously added to menu so we can add new updated items
		
		# Set default quicklist items
		ql = Dbusmenu.Menuitem.new()
		item1 = Dbusmenu.Menuitem.new()
		item1.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Tab")
		item1.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item1.connect ("item-activated", menu_open_new_tab)
		item2 = Dbusmenu.Menuitem.new()
		item2.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Private Tab")
		item2.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item2.connect ("item-activated", menu_open_new_private_tab)
		item3 = Dbusmenu.Menuitem.new()
		item3.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Window")
		item3.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item3.connect ("item-activated", menu_open_new_window)
		ql.child_append (item1)
		ql.child_append (item2)
		ql.child_append (item3)
		
		# Add Mail to menu if an account exists
		if os.path.isfile(home + "/." + args.program + "/mail/accounts.ini"):
			file = open(home + "/." + args.program + "/mail/accounts.ini")
			if "Count=" in file.read():
				item4 = Dbusmenu.Menuitem.new()
				item4.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "Mail")
				item4.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
				item4.connect ("item-activated", menu_open_mail)
				ql.child_append (item4)
		
		if args.speeddial:
			# Reread speeddial.ini since it was flush on the diff
			file = open(home + "/." + args.program + "/speeddial.ini")
			
			# Set Speed Dial menu items for quicklist
			while 1:
				line = file.readline()
				if not line:
					break
				if "Custom Title=" in line:
					pass
				elif "Title=" in line:
					title = str(line[line.find("=")+1:len(line)]).rstrip('\n')
				elif "Url=" in line:
					url = str(line[line.find("=")+1:len(line)]).rstrip('\n')
					item5 = Dbusmenu.Menuitem.new ()
					item5.property_set (Dbusmenu.MENUITEM_PROP_LABEL, title)
					item5.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
					item5.connect ("item-activated", menu_open_speeddial_item, url)
					ql.child_append (item5)
					log("\t" + title + " (" + url + ')', 0)
				pass # do something
			file.close

		# Activate quicklist
		launcher.set_property("quicklist", ql)
		
		# If current_speeddial is empty, then its disabled. Change it to stop processing
		if current_speeddial == "":
			args.quicklist = False


########################################################
# update_tabs()
#
# Description: Get number of open tabs across all windows
########################################################
def update_tabs():
	global current_tabs, tab_count_changed
	tabs = 0
	windows = 0
	
	# Make sure the session file exists before attempting to read it
	if not os.path.isfile(home + "/." + args.program + "/sessions/autosave.win"):
		log("Error: Unable to open " + home + "/." + args.program + "/sessions/autosave.win", 2)
		exit()
	
	try:
		file = open(home + "/." + args.program + "/sessions/autosave.win")
	except IOError:
		pass
	
	line = file.readline();
	while line:
		if "window count" in line:
			tabs = int(line[line.find("=")+1:len(line)])
		elif "type=0" in line:
			windows += 1
		line = file.readline();
	file.close
	tabs = tabs - windows

	# Set number of open tabs across all windows
	if tabs == current_tabs:
		tab_count_changed = False
		return True
	elif tabs > 0:
		if args.tabcount:
			launcher.set_property("count", tabs)
			launcher.set_property("count_visible", True)
		if tabs > current_tabs:
			tab_count_changed = True
		current_tabs = tabs
		log("Updating tab count",0)
	else:
		launcher.set_property("count", 0)
		launcher.set_property("count_visible", False)
		current_tabs = 0
		tab_count_changed = False
	return True


########################################################
# update_progress()
#
# Description: Get number of open tabs across all windows
########################################################
def update_progress():
	return True
#	# Set progress to 42% done 
#	launcher.set_property("progress", 0.42)
#	launcher.set_property("progress_visible", True)


########################################################
# update_urgency()
#
# Description: Get number of open tabs across all windows
########################################################
def update_urgency():
	if not is_opera_focused():
		if tab_count_changed:
			launcher.set_property("urgent", True)
			return
	else:
		launcher.set_property("urgent", False)


########################################################
# get_active_window_title()
#
# Description: Get the currently focused window. Used by
#              update_urgency() to check for Opera.
########################################################
def is_opera_focused():
	global is_first_check
	if is_first_check:
		is_first_check = False
		return True
	
	root_check = ''
	root = subprocess.Popen(['xprop', '-root'],  stdout=subprocess.PIPE)

	if root.stdout != root_check:
		root_check = root.stdout

		for i in root.stdout:
			if '_NET_ACTIVE_WINDOW(WINDOW):' in i:
				id_ = i.split()[4]
				id_w = subprocess.Popen(['xprop', '-id', id_], stdout=subprocess.PIPE)
		id_w.wait()
		buff = []
		for j in id_w.stdout:
			buff.append(j)

		for line in buff:
			match = re.match("WM_NAME\((?P<type>.+)\) = (?P<name>.+)", line)
			if match != None:
				type = match.group("type")
				if type == "STRING" or type == "COMPOUND_TEXT":
					if " - Opera" in match.group("name"):
						return True
	return False

		
########################################################
# get_updates()
#
# Description: Check for updates to apply
########################################################
def get_updates():
	global current_tabs, is_first_check, args
	
	if args.quicklist:
		update_quicklist()
	
	if not is_opera_running():
		launcher.set_property("count_visible", False)
		launcher.set_property("urgent", False)
		
		#initialize some settings so it works properly next time Opera's opened
		current_tabs = 0
		is_first_check = True
		return True
	else:
		if args.tabcount or args.urgency:
			update_tabs()
		if args.progress_bar:
			update_progress()
		if args.urgency:
			update_urgency()
	return True


# Call tab updates
GObject.timeout_add_seconds(1, get_updates)

loop.run()
