# -*- coding: UTF-8 -*-

from . import _
from Plugins.Plugin import PluginDescriptor
from twisted.web.client import downloadPage
from threading import Thread
from enigma import ePicLoad, eServiceReference, eTimer, eServiceCenter, getDesktop, ePoint, eSize, iPlayableService, eListbox
from Screens.Screen import Screen
from Screens.EpgSelection import EPGSelection
from Components.PluginComponent import plugins
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarCueSheetSupport
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.MovieSelection import MovieSelection, SelectionEventInfo
#from Screens import MovieSelection as myMovieSelection
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.ChannelSelection import ChannelContextMenu, OFF, MODE_TV, service_types_tv
from Components.ChoiceList import ChoiceEntryComponent
from Tools.BoundFunction import boundFunction
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.PluginComponent import plugins
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.MovieList import MovieList
from Components.Language import language
from Components.Input import Input
from Components.ServiceEventTracker import InfoBarBase
from Screens.Console import Console
from Screens.InputBox import InputBox
from Components.ProgressBar import ProgressBar
from Components.Sources.StaticText import StaticText
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText, getConfigListEntry, ConfigSelection, ConfigInteger
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from Screens.EventView import EventViewSimple
import os, sys, re 
import gettext, random
import tmdb, urllib
import array, struct, fcntl
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SHUT_RDWR
from event import Event, ShortEventDescriptor, ExtendedEventDescriptor
from time import strftime, localtime, mktime
from meta import MetaParser, getctime, fileSize
import kinopoisk, urllib2
import tmbdYTTrailer

plugin_version = "7.4"

epg_furtherOptions = False
if hasattr(EPGSelection, "furtherOptions"):
	epg_furtherOptions = True


TMDB_LANGUAGE_CODES = {
  'en': 'eng',
  'ru': 'rus',
  'fr': 'fra',
  'bg': 'bul',  
  'it': 'ita',
  'po': 'pol',
  'lv': 'lav',
  'de': 'ger',
  'da': 'dan',
  'nl': 'dut',
  'fi': 'fin',
  'el': 'gre',
  'he': 'heb',
  'hu': 'hun',
  'no': 'nor',
  'pt': 'por',
  'ro': 'ron',
  'sk': 'slo',
  'sl': 'slv',
  'es': 'est',
  'sv': 'swe',
  'tr': 'tur',
  'uk': 'ukr',
  'cz': 'cze'
}


SIOCGIFCONF = 0x8912
BYTES = 4096

TMBDInfoBarKeys = [
	["none",_("NONE"),["KEY_RESERVED"]],
	["Red",_("RED"),["KEY_RED"]],
	["Green",_("GREEN"),["KEY_GREEN"]],
	["Yellow",_("YELLOW"),["KEY_YELLOW"]],
	["Radio",_("RADIO"),["KEY_RADIO"]],
	["Text",_("TEXT"),["KEY_TEXT"]],
	["Tv",_("TV"),["KEY_TV"]],
	["Help",_("HELP"),["KEY_HELP"]],
]

def cutName(eventName=""):
	if eventName:
		eventName = eventName.replace('"', '').replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '').replace('.', '').replace(' | ', '')
		eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '').replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '').replace('(0+)', '').replace('0+', '').replace('+', '')
		return eventName
	return ""

def GetLanguageCode():
	lang = config.plugins.tmbd.locale.value
	return TMDB_LANGUAGE_CODES.get(lang, 'rus')

config.plugins.tmbd = ConfigSubsection()
config.plugins.tmbd.locale = ConfigText(default="ru", fixed_size = False)
config.plugins.tmbd.skins = ConfigSelection(default = "0", choices = [
                        ("0", _("Small poster")), ("1", _("Large poster"))])
config.plugins.tmbd.enabled = ConfigYesNo(default=True)
config.plugins.tmbd.virtual_text = ConfigSelection(default = "0", choices = [
                         ("0", _("< empty >")), ("1", _("< text >"))])
config.plugins.tmbd.menu = ConfigYesNo(default=True)
config.plugins.tmbd.menu_profile = ConfigSelection(default = "0", choices = [
                        ("0", _("only current profile")), ("1", _("List: themoviedb.org / kinopoisk.ru")), ("2", _("List: kinopoisk.ru / themoviedb.org"))])
config.plugins.tmbd.add_tmbd_to_epg = ConfigYesNo(default=False)
config.plugins.tmbd.add_tmbd_to_multi = ConfigYesNo(default=False)
config.plugins.tmbd.add_tmbd_to_graph = ConfigYesNo(default=False)
config.plugins.tmbd.add_ext_menu = ConfigYesNo(default=False)
config.plugins.tmbd.ext_menu_event = ConfigSelection(default = "0", choices = [
                        ("0", _("only current event")), ("1", _("choice now/next event"))])
config.plugins.tmbd.no_event = ConfigYesNo(default=False)
config.plugins.tmbd.test_connect = ConfigYesNo(default=False)
config.plugins.tmbd.exit_key = ConfigSelection(default = "0", choices = [
                        ("0", _("close")), ("1", _("ask user"))])
config.plugins.tmbd.profile = ConfigSelection(default = "0", choices = [
                        ("0", _("themoviedb.org")), ("1", _("kinopoisk.ru (only russian language)"))])
config.plugins.tmbd.position_x = ConfigInteger(default=100)
config.plugins.tmbd.position_y = ConfigInteger(default=100)
config.plugins.tmbd.new_movieselect = ConfigYesNo(default=True)
config.plugins.tmbd.size = ConfigSelection(choices=["285x398", "185x278", "130x200", "104x150"], default="130x200")
config.plugins.tmbd.hotkey = ConfigSelection([(x[0],x[1]) for x in TMBDInfoBarKeys], "none")
config.plugins.tmbd.movielist_profile = ConfigSelection(default = "1", choices = [
                        ("0", _("only current profile")), ("1", _("List: themoviedb.org / kinopoisk.ru")), ("2", _("List: kinopoisk.ru / themoviedb.org"))])
config.plugins.tmbd.kinopoisk_data = ConfigSelection(choices = [("1", _("Press OK"))], default = "1")
config.plugins.tmbd.yt_setup = ConfigSelection(choices = [("1", _("Press OK"))], default = "1")
config.plugins.tmbd.add_tmbd_to_nstreamvod = ConfigYesNo(default=False)
config.plugins.tmbd.add_vcs_to_nstreamvod = ConfigYesNo(default=False)
config.plugins.tmbd.show_in_furtheroptionsmenu = ConfigYesNo(default=True)
if epg_furtherOptions:
	config.plugins.tmbd.yt_event_menu = ConfigSelection(default="3", choices = [("0", _("disabled")),("1", _("EPGSelection (context menu)")), ("2", _("EventView (context menu)/EventInfo plugins")), ("3", _("EPGSelection/EventView/EventInfo plugins"))])
else:
	config.plugins.tmbd.yt_event_menu = ConfigSelection(default="2", choices = [("0", _("disabled")), ("2", _("EventView (context menu)/EventInfo plugins"))])
config.plugins.tmbd.yt_start = ConfigSelection(default = "0", choices = [
                        ("0", _("show list")), ("1", _("run first"))])
config.plugins.tmbd.cover_dir = ConfigText(default="/media/hdd/", fixed_size = False)


SKIN = """
	<screen position="0,0" size="130,200" zPosition="10" flags="wfNoBorder" backgroundColor="#ff000000" >
		<widget name="background" position="0,0" size="130,200" zPosition="1" backgroundColor="#00000000" />
		<widget name="preview" position="0,0" size="130,200" zPosition="2" alphatest="blend"/>
	</screen>"""

_session = None
eventname = ""
baseGraphMultiEPG__init__ = None

def GraphMultiEPGInit():
	global baseGraphMultiEPG__init__
	try:
		from Plugins.Extensions.GraphMultiEPG.GraphMultiEpg import GraphMultiEPG
	except ImportError:
		return
	if baseGraphMultiEPG__init__ is None:
		baseGraphMultiEPG__init__ = GraphMultiEPG.__init__
	GraphMultiEPG.__init__ = GraphMultiEPG__init__

def GraphMultiEPG__init__(self, session, services, zapFunc=None, bouquetChangeCB=None, bouquetname=""):
	try:
		baseGraphMultiEPG__init__(self, session, services, zapFunc, bouquetChangeCB, bouquetname)
	except:
		baseGraphMultiEPG__init__(self, session, services, zapFunc, bouquetChangeCB)
	if config.plugins.tmbd.add_tmbd_to_graph.value:
		def upPressed():
			try:
				self["list"].moveTo(eListbox.moveUp)
			except:
				pass
		def downPressed():
			try:
				self["list"].moveTo(eListbox.moveDown)
			except:
				pass
		def showTMBD():
			from Plugins.Extensions.TMBD.plugin import TMBD
			from Plugins.Extensions.TMBD.plugin import KinoRu
			cur = self["list"].getCurrent()
			if cur and cur[0] is not None:
				name2 = cur[0].getEventName()
				name3 = name2.split("(")[0].strip()
				eventname = cutName(name3)
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname, False)
				else:
					self.session.open(KinoRu, eventname, False)
		self["tmbd_actions"] = HelpableActionMap(self, "EPGSelectActions",
				{
					"info": (showTMBD, _("Lookup in TMBD")),
				}, -1)
		self["tmbdActions"] = HelpableActionMap(self, "WizardActions",
				{
				"up":      (upPressed, _("Go to previous service")),
				"down":    (downPressed,  _("Go to next service"))
				}, -1)

basenStreamVOD__init__ = None
def nStreamVODInit():
	global basenStreamVOD__init__
	try:
		from Plugins.Extensions.nStreamVOD.plugin import nPlaylist
	except ImportError:
		pass
	else:
		if basenStreamVOD__init__ is None:
			basenStreamVOD__init__ = nPlaylist.__init__
			nPlaylist.__init__ = nPlaylist__init__
			nPlaylist.AnswernStreamVOD = AnswernStreamVOD

def nPlaylist__init__(self, session):
	try:
		basenStreamVOD__init__(self, session)
		if config.plugins.tmbd.add_tmbd_to_nstreamvod.value:
			def SelectionInfo():
				from Screens.ChoiceBox import ChoiceBox
				if config.plugins.tmbd.add_vcs_to_nstreamvod.value:
					list = [
						(_("search in TMBD"), "tmbd"),
						(_("standard info"), "info"),
						(_("open plugin VCS"), "vcs"),
					]
				else:
					list = [
						(_("search in TMBD"), "tmbd"),
						(_("standard info"), "info"),
					]
				self.session.openWithCallback(self.AnswernStreamVOD,ChoiceBox,title= _("Select action:"), list = list)
			self["tmbd_actions"] = HelpableActionMap(self, "EPGSelectActions",
					{
						"info": SelectionInfo,
					}, -1)
	except:
		pass

def AnswernStreamVOD(self, ret):
	ret = ret and ret[1]
	if ret:
		if ret == "tmbd":
			try:
				selected_channel = self.channel_list[self.mlist.getSelectionIndex()]
			except:
				selected_channel = None
			if selected_channel is not None:
				try:
					event = selected_channel[1]
				except:
					event = None
				if event is not None and event != "":
					try:
						from Plugins.Extensions.TMBD.plugin import TMBD
						from Plugins.Extensions.TMBD.plugin import KinoRu
						eventname = cutName(event)
						if config.plugins.tmbd.profile.value == "0":
							self.session.open(TMBD, eventname, False)
						else:
							self.session.open(KinoRu, eventname, False)
					except:
						pass
		elif ret == "info":
			try:
				self.show_more_info()
			except:
				pass
		elif ret == "vcs":
			try:
				from Plugins.Extensions.VCS.plugin import show_choisebox
				show_choisebox(self.session)
			except:
				pass
		else:
			pass

def_SelectionEventInfo_updateEventInfo = None

def new_SelectionEventInfo_updateEventInfo(self):
	serviceref = self.getCurrent()
	if config.plugins.tmbd.new_movieselect.value:
		if serviceref and serviceref.type == eServiceReference.idUser+1:
			import os
			pathname = serviceref.getPath()
			if len(pathname) > 2 and os.path.exists(pathname[:-2]+'eit'):
				serviceref = eServiceReference(serviceref.toString())
				serviceref.type = eServiceReference.idDVB
	self["Service"].newService(serviceref)

def_MovieSelection_showEventInformation = None
	
def new_MovieSelection_showEventInformation(self):
	evt = self["list"].getCurrentEvent()
	if not evt:
		l = self["list"].l.getCurrentSelection()
		if l is not None:
			serviceref = l[0]
			pathname = serviceref and serviceref.getPath() or ''
			if len(pathname) > 2 and os.path.exists(pathname[:-2]+'eit'):
				serviceref = eServiceReference(serviceref.toString())
				serviceref.type = eServiceReference.idDVB
				info = eServiceCenter.getInstance().info(serviceref)
				evt = info and info.getEvent(serviceref)
	if evt:
		self.session.open(EventViewSimple, evt, ServiceReference(self.getCurrent()))

baseEPGSelection__init__ = None
def EPGSelectionInit():
	global baseEPGSelection__init__
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	EPGSelection.__init__ = EPGSelection__init__

def EPGSelection__init__(self, session, service=None, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, EPGtype=None, StartBouquet=None , StartRef=None, bouquets=None):
	try:
		baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
	except:
		baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB,EPGtype, StartBouquet, StartRef, bouquets)
	if self.type == EPG_TYPE_SINGLE and config.plugins.tmbd.add_tmbd_to_epg.value:
		def redPressed():
			from Plugins.Extensions.TMBD.plugin import TMBD
			from Plugins.Extensions.TMBD.plugin import KinoRu
			cur = self["list"].getCurrent()
			if cur[0] is not None:
				name2 = cur[0].getEventName()
				name3 = name2.split("(")[0].strip()
				eventname = cutName(name3)
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname, False)
				else:
					self.session.open(KinoRu, eventname, False)

		self["tmbdActions"] = ActionMap(["EPGSelectActions"],
				{
					"info": redPressed,
				})

	elif self.type == EPG_TYPE_MULTI and config.plugins.tmbd.add_tmbd_to_multi.value:
		def KeyInfoPressed():
			from Plugins.Extensions.TMBD.plugin import TMBD
			from Plugins.Extensions.TMBD.plugin import KinoRu
			cur = self["list"].getCurrent()
			if cur[0] is not None:
				name2 = cur[0].getEventName()
				name3 = name2.split("(")[0].strip()
				eventname = cutName(name3)
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname, False)
				else:
					self.session.open(KinoRu, eventname, False)

		self["Tmbdactions"] = ActionMap(["EPGSelectActions"],
				{
					"info": KeyInfoPressed,
				})

baseChannelContextMenu__init__ = None
def TMBDChannelContextMenuInit():
	global baseChannelContextMenu__init__
	if baseChannelContextMenu__init__ is None:
		baseChannelContextMenu__init__ = ChannelContextMenu.__init__
	ChannelContextMenu.__init__ = TMBDChannelContextMenu__init__
	ChannelContextMenu.showServiceInformations2 = showServiceInformations2
	ChannelContextMenu.profileContextMenuCallback = profileContextMenuCallback
	ChannelContextMenu.profileMenuCallback = profileMenuCallback

def TMBDChannelContextMenu__init__(self, session, csel):
	baseChannelContextMenu__init__(self, session, csel)
	if csel.mode == MODE_TV:
		current = csel.getCurrentSelection()
		current_root = csel.getRoot()
		current_sel_path = current.getPath()
		current_sel_flags = current.flags
		inBouquetRootList = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1
		inBouquet = csel.getMutableList() is not None
		isPlayable = not (current_sel_flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
		if isPlayable and current and current.valid():
			if config.plugins.tmbd.menu.value:
				if config.plugins.tmbd.menu_profile.value == "0":
					callFunction = self.showServiceInformations2 
					self["menu"].list.insert(1, ChoiceEntryComponent(text = (_("TMBD Details"), boundFunction(callFunction,1))))
				else:
					callFunction = self.profileContextMenuCallback 
					self["menu"].list.insert(1, ChoiceEntryComponent(text = (_("TMBD Details"), boundFunction(callFunction,1))))
			else:
				pass

def showServiceInformations2(self, eventName="", profile = False):
		global eventname
		s = self.csel.servicelist.getCurrent()  
		info = s and eServiceCenter.getInstance().info(s)
		event = info and info.getEvent(s)
		if event != None:
			try:
				epg_name = event.getEventName() or ''
				eventname = cutName(epg_name)
				eventName = eventname
				if config.plugins.tmbd.menu_profile.value == "0":
					if config.plugins.tmbd.profile.value == "0":
						self.session.open(TMBD, eventName)
					else:
						self.session.open(KinoRu, eventName)
				else:
					if profile:
						self.session.open(KinoRu, eventName)
					else:
						self.session.open(TMBD, eventName)
			except ImportError as ie:
				pass

def profileContextMenuCallback(self, add):
	if config.plugins.tmbd.menu_profile.value == "1":
		options = [
				(_("themoviedb.org"), boundFunction(self.showServiceInformations2, profile = False)),
				(_("kinopoisk.ru"), boundFunction(self.showServiceInformations2, profile = True)),
			]
	elif config.plugins.tmbd.menu_profile.value == "2":
		options = [
				(_("kinopoisk.ru"), boundFunction(self.showServiceInformations2, profile = True)),
				(_("themoviedb.org"), boundFunction(self.showServiceInformations2, profile = False)),
			]
	self.session.openWithCallback(self.profileMenuCallback, ChoiceBox, title= _("Choice profile in search:"), list = options)

def profileMenuCallback(self, ret):
	ret and ret[1]()

class TMBDChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(
				self.epgClosed,
				TMBDEPGSelection,
				ref,
				openPlugin = False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class TMBDEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin = True):
		EPGSelection.__init__(self, session, ref)
		self.skinName = "EPGSelection"
		self["key_red"].setText(_("Lookup in TMBD"))
		self.openPlugin = openPlugin

	def zapTo(self):
		global eventname
		eventname = ""
		cur = self["list"].getCurrent()
		evt = cur and cur[0]
		if evt != None:
			event = evt.getEventName()
			name = event.split("(")[0].strip()
			eventname = cutName(name)
		if self.openPlugin:
			if config.plugins.tmbd.profile.value == "0":
				self.session.open(TMBD, eventname)
			else:
				self.session.open(KinoRu, eventname)
		else:
			self.close(eventname)

testOK = None
movie2 = ""

class TMBD(Screen):
	skin_hd1 = """
		<screen name="TMBD" position="90,90" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="760,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="790,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="790,10"  size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" halign="left" name="ratinglabel" foregroundColor="#00f0b400" position="790,34" size="210,23" transparent="1" />
		<widget font="Regular;20" name="voteslabel" halign="left" position="790,57" size="290,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,60" size="285,398" />
		<widget name="menu" position="325,100" scrollbarMode="showOnDemand" size="750,130" zPosition="3"  selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,59" size="570,35" font="Regular;19" transparent="1" />  
		<widget font="Regular;20" name="castlabel" position="320,245" size="760,240" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="320,77" size="760,180" transparent="1" />
		<widget font="Regular;18" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""
	skin_hd = """
		<screen name="TMBD" position="90,90" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="760,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="790,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="790,10" size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" foregroundColor="#00f0b400" halign="left" name="ratinglabel" position="790,34" size="210,23" transparent="1" />
		<widget font="Regular;20" halign="left" name="voteslabel" position="790,57" size="290,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,60" size="110,180" />
		<widget name="menu" position="170,100" scrollbarMode="showOnDemand" size="920,130" zPosition="3" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,59" size="570,35" font="Regular;19" transparent="1" />
		<widget font="Regular;20" name="castlabel" position="20,245" size="1060,240" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="164,77" size="920,180" transparent="1" />
		<widget font="Regular;18" foregroundColor="#00cccccc" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""
	skin_sd = """
		<screen name="TMBD" position="center,center" size="600,420" title="TMBD Details Plugin" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="565,5" zPosition="0" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="565,33" zPosition="1" size="35,25" alphatest="on" />
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
		<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
		<widget name="title" position="10,40" size="330,45" valign="center" font="Regular;20" transparent="1"/>
		<widget name="extralabel" position="105,90" size="485,140" font="Regular;18" />
		<widget name="castlabel" position="10,235" size="580,155" font="Regular;18"  zPosition="3"/>
		<widget name="ratinglabel" position="340,62" size="250,20" halign="center" font="Regular;18" foregroundColor="#f0b400"/>
		<widget name="statusbar" position="10,404" size="580,16" font="Regular;16" foregroundColor="#cccccc" />
		<widget font="Regular;16" halign="center" name="voteslabel" foregroundColor="#00f0b400" position="380,404" size="210,16" transparent="1" />
		<widget name="poster" position="4,90" size="96,140" alphatest="on" />
		<widget name="menu" position="105,90" size="485,140" zPosition="2" scrollbarMode="showOnDemand" />
		<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="340,40" zPosition="0" size="210,21" transparent="1" alphatest="on" />
		<widget name="stars" position="340,40" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" transparent="1" />
	</screen>"""

	def __init__(self, session, eventName, callbackNeeded=False, movielist = False):
		Screen.__init__(self, session)
		self.skin = self.setSkin()
		print self.skin
		self.eventName = eventName
		self.curResult = False
		self.noExit = False
		self.onShow.append(self.selectionChanged)
		self.movielist = movielist
		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""
		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1
		self.working = False
		self["title"] = Label("")
		self["title"].setText(_("The Internet Movie Database"))
		self["detailslabel"] = ScrollLabel("")
		self["castlabel"] = ScrollLabel("")
		self["extralabel"] = ScrollLabel("")
		self["statusbar"] = Label("")
		self["ratinglabel"] = Label("")
		self["voteslabel"] = Label("")
		self.resultlist = []
		self["menu"] = MenuList(self.resultlist)
		self["menu"].hide()
		self["menu"].onSelectionChanged.append(self.selectionChanged)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Manual input"))
		self.Page = 0
		self.working = False
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.TMBDPoster)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
		{
			"ok": self.showExtras,
			"cancel": self.exit2,
			"down": self.pageDown,
			"up": self.pageUp,
			"left": self.scrollLabelPageUp,
			"right": self.scrollLabelPageDown,
			"red": self.exit,
			"green": self.searchYttrailer2,
			"yellow": self.showExtras,
			"blue": self.openVirtualKeyBoard,
			"contextMenu": self.contextMenuPressed,
			"showEventInfo": self.aboutAutor
		}, -1)
		
		self.setTitle(_("Profile: themoviedb.org"))
		self.removCovers()
		self.tmdb3 = tmdb.init_tmdb3()
		if self.tmdb3 is None:
			self["statusbar"].setText(_("Unknown error!"))
			return
		self.testThread = None
		self.testTime = 2.0		# 1 seconds
		self.testHost = "www.themoviedb.org"
		self.testPort = 80		# www port
		if config.plugins.tmbd.test_connect.value:
			self.TestConnection()
		else:
			self.getTMBD()

	def setSkin(self):
		try:
			screenWidth = getDesktop(0).size().width()
		except:
			screenWidth = 720
		if screenWidth >= 1280:
			if config.plugins.tmbd.skins.value == "0":
				return TMBD.skin_hd
			if config.plugins.tmbd.skins.value == "1":
				return TMBD.skin_hd1
		else:
			return TMBD.skin_sd

	def TestConnection(self):
		self.testThread = Thread(target=self.test)
		self.testThread.start()
		
	def get_iface_list(self):
		names = array.array('B', '\0' * BYTES)
		sck = socket(AF_INET, SOCK_DGRAM)
		bytelen = struct.unpack('iL', fcntl.ioctl(sck.fileno(), SIOCGIFCONF, struct.pack('iL', BYTES, names.buffer_info()[0])))[0]
		sck.close()
		namestr = names.tostring()
		return [namestr[i:i+32].split('\0', 1)[0] for i in range(0, bytelen, 32)]

	def test(self):
		global testOK
		link = "down"
		for iface in self.get_iface_list():
			if "lo" in iface: continue
			if os.path.exists("/sys/class/net/%s/operstate"%(iface)):
				fd = open("/sys/class/net/%s/operstate"%(iface), "r")
				link = fd.read().strip()
				fd.close()
			if link != "down": break
		if link != "down":
			s = socket(AF_INET, SOCK_STREAM)
			s.settimeout(self.testTime)
			try:
				testOK = not bool(s.connect_ex((self.testHost, self.testPort)))
			except:
				testOK = None
			if not testOK:
				print 'Conection failed'
				self.resetLabels()
				self["statusbar"].setText(_("No connect to www.themoviedb.org"))
				self["title"].setText("")
				return
			else:
				s.shutdown(SHUT_RDWR)
				self.getTMBD()
			s.close()
		else:
			testOK = None
			self.resetLabels()
			self["statusbar"].setText(_("Not found network connection..."))
			self["title"].setText("")
			return

	def exit(self):
		self.close()

	def exit2(self):
		if config.plugins.tmbd.exit_key.value == "1":
			self.session.openWithCallback(self.exitConfirmed, MessageBox, _("Close plugin?"), MessageBox.TYPE_YESNO)
		else:
			self.exit()

	def exitConfirmed(self, answer):
		if answer:
			self.close()

	def aboutAutor(self):
		self.session.open(MessageBox, _("TMBD Details Plugin\nDeveloper: Nikolasi,vlamo,Dima73\n(c)2012"), MessageBox.TYPE_INFO)

	def removCovers(self):
		if os.path.exists('/tmp/preview.jpg'):
			try:
				os.remove('/tmp/preview.jpg')
			except:
				pass

	def resetLabels(self):
		try:
			self["detailslabel"].setText("")
			self["ratinglabel"].setText("")
			self["title"].setText(_("Search in themoviedb.org ,please wait ..."))
			self["castlabel"].setText("")
			self["extralabel"].setText("")
			self["voteslabel"].setText("")
			self["key_green"].setText("")
		except:
			pass
		self.ratingstars = -1

	def pageUp(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
			self["castlabel"].pageUp()
		if self.Page == 1:
			self["extralabel"].pageUp()

	def pageDown(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
			self["castlabel"].pageUp()
		if self.Page == 1:
			self["extralabel"].pageDown()

	def scrollLabelPageUp(self):
		self["castlabel"].pageUp()

	def scrollLabelPageDown(self):
		self["castlabel"].pageDown()

	def showMenu(self):
		global eventname, total
		self.noExit = False
		if self.curResult:
			self["menu"].show()
			self["ratinglabel"].show()
			self["castlabel"].show()
			self["poster"].show()
			self["extralabel"].hide()
			self["title"].setText(_("Search results for: %s") % (eventname))
			if total > 1:
				self["detailslabel"].setText(_("Please select the matching entry:"))
			self["detailslabel"].show()
			self["key_blue"].setText(_("Manual input"))
			if self.movielist:
				self["key_green"].setText(_("Save info / poster"))
			else:
				self["key_green"].setText(_("Search Trailer"))
			self["key_yellow"].setText(_("Show movie details"))
			if self.ratingstars > 0:
				self["starsbg"].show()
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)
			self.working = True

	def showExtras(self):
		if self.curResult:
			if not self.noExit:
				self.Page = 1
				self.noExit = True
				self["menu"].hide()
				self["extralabel"].show()
				self["detailslabel"].hide()
				self["key_yellow"].setText("")
				self.showExtras2()
			else:
				self.Page = 0
				self.noExit = False
				self.showMenu()

	def selectionChanged(self):
		self["poster"].hide()
		self["stars"].hide()
		self["starsbg"].hide()
		self["ratinglabel"].hide()
		self["castlabel"].hide()
		current = self["menu"].l.getCurrentSelection()
		if current and self.curResult:
			try:
				movie = current[1]
				jpg_file = "/tmp/preview.jpg"
				try:
					image = movie.poster
					cover_url = None
					if image is not None:
						cover_url = image.geturl()
					if cover_url:
						urllib.urlretrieve(cover_url, jpg_file)
				except:
					pass
				self.refreshTimer.start(100, True)
				Casttext = ""
				try:
					name = movie.title.encode('utf-8', 'ignore')
				except:
					name = ''
				if name != '':
					try:
						Casttext = "%s / " % name
					except:
						pass
				try:
					released = movie.releasedate.year
				except:
					released = ''
				if released != '':
					try:
						released_text = _("Appeared: ") + '%s ' % released
						Casttext += released_text
					except:
						pass
				try:
					runtime = movie.runtime
				except:
					runtime = ''
				if runtime != '':
					try:
						runtime_text = "%s\n\n" % self.textNo(str(runtime))
						Casttext += runtime_text
					except:
						pass
				try:
					description = movie.overview
				except:
					description = ''
				if description != '':
					try:
						description_text = description.encode('utf-8', 'ignore')
						Casttext += description_text
					except:
						pass
				if Casttext != '':
					self["castlabel"].setText(Casttext)
					self["castlabel"].show()
				Ratingtext = _("no user rating yet")
				try:
					rating = str(movie.userrating)
				except:
					rating = ''
				if rating != '' and rating != "0.0":
					try:
						Ratingtext = _("User Rating") + ": " + rating + " / 10"
						self.ratingstars = int(10*round(float(rating.replace(',','.')),1))
						if self.ratingstars > 0:
							self["stars"].setValue(self.ratingstars)
							self["stars"].show()
							self["starsbg"].show()
					except:
						pass
				self["ratinglabel"].show()
				self["ratinglabel"].setText(Ratingtext)
				Votestext = ""
				try:
					votes = str(movie.votes)
				except:
					votes = ''
				if votes != '' and votes != "0":
					try:
						Votestext = _("Votes") + ": " + votes + _(" times")
					except:
						pass
				self["voteslabel"].setText(Votestext)
			except:
				pass

	def showExtras2(self):
		if self.curResult:
			current = self["menu"].l.getCurrentSelection()
			if current:
				movie = current[1]
				self["key_yellow"].setText(_("Show search results"))
				try:
					namedetals = current[0]
					self["title"].setText(_("Details for: %s") % (namedetals))
				except:
					pass
				Extratext = ""
				try:
					genres = [ x.name.encode('utf-8', 'ignore') for x in movie.genres ]
				except:
					genres =[]
				if len(genres) > 0:
					try:
						genre = ', '.join(genres)
						Extratext += "%s: %s\n" % (_("Genre"), genre)
					except:
						pass
				try:
					crew = [ x.name.encode('utf-8', 'ignore') for x in movie.crew if x.job == 'Director' ]
				except:
					crew =[]
				if len(crew) > 0:
					try:
						directors = ', '.join(crew)
						Extratext += "%s: %s\n" % (_("Director"), directors)
					except:
						pass
				try:
					crew1 = [ x.name.encode('utf-8', 'ignore') for x in movie.crew if x.job == 'Producer' ]
				except:
					crew1 =[]
				if len(crew1) > 0:
					try:
						producers = ', '.join(crew1)
						Extratext += "%s: %s\n" % (_("Producers"), producers)
					except:
						pass
				try:
					cast = [ x.name.encode('utf-8', 'ignore') for x in movie.cast ]
				except:
					cast =[]
				if len(cast) > 0:
					try:
						actors = ', '.join(cast)
						Extratext += "%s: %s\n" % (_("Actors"), actors)
					except:
						pass
				Extratext2 = ""
				try:
					studios = [ x.name.encode('utf-8', 'ignore') for x in movie.studios ]
				except:
					studios =[]
				if len(studios) > 0:
					try:
						studio = ', '.join(studios)
						Extratext2 = "%s: %s\n" % (_("Studios"), studio)
					except:
						pass
				try:
					cert = movie.releases
					if cert:
						certification = tmdb.decodeCertification(movie.releases)
					else:
						certification = ''
				except:
					certification = ''
				if certification != '' and certification != None:
					try:
						Extratext2 += "%s: %s\n" % (_("Certification"), certification)
					except:
						pass
				try:
					countries = [ x.name for x in movie.countries ]
				except:
					countries = []
				if len(countries) > 0:
					try:
						country = ''
						for name in countries:
							country += '%s, '% str(name)
						if country != '':
							country = country[:-2]
							Extratext2 += "%s: %s\n" % (_("Country"), country)
					except:
						pass
				self["extralabel"].setText("%s%s" % (Extratext2, Extratext))

	def removmenu(self):
		list = [
			(_("Current poster and info"), self.removcurrent),
			(_("Only current poster"), self.removcurrentposter),
			(_("Only current info"), self.removcurrentinfo),
			(_("All posters for movie"), self.removresult),
		]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
			title= _("What exactly do you want to delete?"),
		)	

	def contextMenuPressed(self):
		if self.movielist:
			list = [
				(_("Text editing"), self.openKeyBoard),
				(_("Select from Favourites"), self.openChannelSelection),
				(_("Search Trailer"), self.searchYttrailer3),
				(_("Remove poster / info"), self.removmenu),
				(_("Settings"), self.Menu2),
			]
		else:
			list = [
				(_("Text editing"), self.openKeyBoard),
				(_("Select from Favourites"), self.openChannelSelection),
				(_("Settings"), self.Menu2),
			]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
			title= _("Select action:"),
		)

	def Menu2(self):
		self.session.openWithCallback(self.workingFinished, TMBDSettings)

	def saveresult(self):
		global name
		list = [
			(_("Yes"), self.savePosterInfo),
			(_("Yes,but write new meta-file"), self.writeMeta),
			(_("No"), self.exitChoice),
		]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title= _("Save poster and info for:\n %s ?") % (name),
			list = list,
		)

	def exitChoice(self):
		self.close()

	def savePosterInfo(self):
		global name
		import os
		import shutil
		if self.curResult:
			self.savedescrip()
		dir = config.plugins.tmbd.cover_dir.value + 'covers'
		if not fileExists(dir):
			try:
				os.makedirs(dir)
			except OSError:
				pass
		if fileExists(dir):
				if fileExists("/tmp/preview.jpg"):
					try:
						shutil.copy2("/tmp/preview.jpg", dir + "/" + name + ".jpg")
						self.session.open(MessageBox, _("Poster %s saved!") % (name), MessageBox.TYPE_INFO, timeout=2)
					except:
						pass

	def writeMeta(self):
		if self.curResult:
			global movie2, eventname
			Extratext2 = ""
			namedetals2 = ""
			if len(movie2):
					TSFILE = movie2
			else:
				return
			current = self["menu"].l.getCurrentSelection()
			if current:
				movie = current[1]
				try:
					namedetals = current[0].decode('utf-8', 'replace').encode('utf-8', 'ignore')
				except:
					return
				if not movie2.endswith(".ts"):
					if namedetals2 != "":
						Extratext2 = "%s /" % ( namedetals2)
				try:
					genres = [ x.name.encode('utf-8', 'ignore') for x in movie.genres ]
				except:
					genres =[]
				if len(genres) > 0:
					try:
						genre = ', '.join(genres)
						Extratext2 += " %s /" % ( genre)
					except:
						pass
				try:
					countries = [ x.name for x in movie.countries ]
				except:
					countries = []
				if len(countries) > 0:
					try:
						country = ''
						for name in countries:
							country += '%s, '% str(name)
						if country != '':
							country = country[:-2]
							Extratext2 += " %s /" % (country)
					except:
						pass
				try:
					cast = [ x.name.encode('utf-8', 'ignore') for x in movie.cast ]
				except:
					cast =[]
				if len(cast) > 0:
					try:
						actors = ', '.join(cast)
						Extratext2 += " %s" % (actors)
					except:
						pass
				metaParser = MetaParser();
				metaParser.name = namedetals2
				metaParser.description = Extratext2;
				if os.path.exists(TSFILE + '.meta') and movie2.endswith(".ts"):
					readmetafile = open("%s.meta"%(movie2), "r")
					linecnt = 0
					line = readmetafile.readline()
					if line:
						line = line.strip()
						if linecnt == 0:
							metaParser.ref = eServiceReference(line)
					else:
						metaParser.ref = eServiceReference('1:0:0:0:0:0:0:0:0:0:')
					readmetafile.close()
				else:
					metaParser.ref = eServiceReference('1:0:0:0:0:0:0:0:0:0:')
				metaParser.time_create = getctime(TSFILE);
				metaParser.tags = '';
				metaParser.length = 0;
				metaParser.filesize = fileSize(TSFILE);
				metaParser.service_data = '';
				metaParser.data_ok = 1;
				metaParser.updateMeta(TSFILE);
				self.session.open(MessageBox, _("Write to new meta-file for:\n") + "%s" % (TSFILE), MessageBox.TYPE_INFO, timeout=3)
				self.timer = eTimer()
				self.timer.callback.append(self.savePosterInfo)
				self.timer.start(1500, True)

	def textNo2(self, text):
		try:
			if text == None or text == "0":
				return (_('0 min.'))
			else:
				return text + _(" min.")
		except:
			return ''

	def savedescrip(self):
		global  movie2
		descrip = ""
		Extratext = ""
		namedetals = ""
		if len(movie2):
				EITFILE = movie2[:-2] + 'eit'
		else:
			return
		current = self["menu"].l.getCurrentSelection()
		if current:
			movie = current[1]
			try:
				namedetals = current[0].decode('utf-8', 'replace').encode('utf-8', 'ignore')
			except:
				return
			try:
				countries = [ x.name for x in movie.countries ]
			except:
				countries = []
			if len(countries) > 0:
				try:
					country = ''
					for name in countries:
						country += '%s, '% str(name)
					if country != '':
						country = country[:-2]
						Extratext = "%s %s\n" % (_("Country:"), country)
				except:
					pass
			try:
				genres = [ x.name.encode('utf-8', 'ignore') for x in movie.genres ]
			except:
				genres =[]
			if len(genres) > 0:
				try:
					genre = ', '.join(genres)
					Extratext += "%s %s\n" % (_("Genre:"), genre)
				except:
					pass
			try:
				description = movie.overview
			except:
				description = ''
			if description != '':
				try:
					description_text = description.encode('utf-8', 'ignore')
					descrip = " %s\n" % description_text
				except:
					pass
			try:
				runtime = movie.runtime
			except:
				runtime = ''
			if runtime != '':
				try:
					runtime_text = "%s" % self.textNo2(str(runtime))
					if runtime_text != '':
						descrip += " %s" % (runtime_text)
				except:
					pass
			try:
				rating = str(movie.userrating)
				votes = str(movie.votes)
			except:
				rating = ''
				votes = ''
			if rating != '' and rating != "0.0":
				try:
					descrip += _(" User Rating: ") + rating + "/10" + _(" (%s times)\n") % (votes)
				except:
					pass
			try:
				cast = [ x.name.encode('utf-8', 'ignore') for x in movie.cast ]
			except:
				cast =[]
			if len(cast) > 0:
				try:
					actors = ', '.join(cast)
					descrip += " %s %s\n" % (_("Actors:"), actors)
				except:
					pass
			Extratext = Extratext.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			Extratext = self.Cutext(Extratext)
			descrip = descrip.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			namedetals = namedetals.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			sed = ShortEventDescriptor([]);
			sed.setIso639LanguageCode(GetLanguageCode());
			sed.setEventName(namedetals);
			sed.setText(Extratext);
			eed = ExtendedEventDescriptor([]);
			eed.setIso639LanguageCode(GetLanguageCode());
			eed.setText(descrip);
			newEvent = Event();
			newEvent.setShortEventDescriptor(sed);
			newEvent.setExtendedEventDescriptor(eed);
			ret = newEvent.saveToFile(EITFILE);
			self.session.open(MessageBox, _("Write event to new eit-file:\n") + "%s\n" % (EITFILE) + _("%d bytes") % (ret), MessageBox.TYPE_INFO, timeout=3)

	def Cutext(self, text):
		if text > 0:
			return text[:179]
		else:
			return text

	def removcurrent(self):
		global name
		self.session.openWithCallback(self.removcurrentConfirmed, MessageBox, _("Remove current poster and info for:\n%s ?") % (name), MessageBox.TYPE_YESNO)

	def removcurrentposter(self):
		global movie2, name
		if len(movie2):
			dir_cover = config.plugins.tmbd.cover_dir.value + 'covers/'
			if movie2.endswith(".ts"):
				if os.path.exists(movie2 + '.meta'):
					try:
						readmetafile = open("%s.meta"%(movie2), "r")
						name_cur = readmetafile.readline()[0:-1]
						name_cover = name_cur + '.jpg'
					except:
						name_cover = ""
					readmetafile.close()
				else:
					name_cover = name + '.jpg'
			else:
					name_cover = name + '.jpg'
			remove_jpg = dir_cover + name_cover
			if os.path.exists(remove_jpg):
				try:
					os.remove(remove_jpg)
					self.session.open(MessageBox, _("%s poster removed!") % (remove_jpg), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
		else:
			return

	def removcurrentinfo(self):
		global movie2, name
		if len(movie2):
			remove_eit = movie2[:-2] + 'eit'
			if os.path.exists(remove_eit):
				try:
					os.remove(remove_eit)
					self.session.open(MessageBox, _("%s eit-file removed!") % (remove_eit), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
			remove_meta = movie2 + '.meta'
			if os.path.exists(remove_meta):
				try:
					os.remove(remove_meta)
					self.session.open(MessageBox, _("%s meta-file removed!") % (remove_meta), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
		else:
			return

	def removcurrentConfirmed(self, confirmed):
		if not confirmed:
			return
		else:
			global movie2, name
			if len(movie2):
				dir_cover = config.plugins.tmbd.cover_dir.value + 'covers/'
				remove_eit = movie2[:-2] + 'eit'
				if os.path.exists(remove_eit):
					try:
						os.remove(remove_eit)
						self.session.open(MessageBox, _("%s eit-file removed!") % (remove_eit), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
				if movie2.endswith(".ts"):
					if os.path.exists(movie2 + '.meta'):
						try:
							readmetafile = open("%s.meta"%(movie2), "r")
							name_cur = readmetafile.readline()[0:-1]
							name_cover = name_cur + '.jpg'
						except:
							name_cover = ""
						readmetafile.close()
					else:
						name_cover = name + '.jpg'
				else:
					name_cover = name + '.jpg'
				remove_jpg = dir_cover + name_cover
				if os.path.exists(remove_jpg):
					try:
						os.remove(remove_jpg)
						self.session.open(MessageBox, _("%s poster removed!") % (remove_jpg), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
				remove_meta = movie2 + '.meta'
				if os.path.exists(remove_meta):
					try:
						os.remove(remove_meta)
						self.session.open(MessageBox, _("%s meta-file removed!") % (remove_meta), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
			else:
				return

	def removresult(self):
		self.session.openWithCallback(self.removresultConfirmed, MessageBox, _("Remove all posters?"), MessageBox.TYPE_YESNO)

	def removresultConfirmed(self, confirmed):
		import os
		import shutil
		if not confirmed:
			return
		else:
			dir = config.plugins.tmbd.cover_dir.value + 'covers'
			if fileExists(dir):
				try:
					shutil.rmtree(dir)
					self.session.open(MessageBox, _("All posters removed!"), MessageBox.TYPE_INFO, timeout=3)
				except OSError:
					pass

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def searchYttrailer3(self):
		self.searchYttrailer()

	def searchYttrailer2(self):
		if self.movielist and self.curResult:
			self.saveresult()
		else:
			self.searchYttrailer()

	def yesNo(self, answer):
		if answer is True:
			self.yesInstall()

	def yesInstall(self):
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/TMBD/enigma2-plugin-extensions-yttrailer_2.0_all.ipk")):
			cmd = "opkg install -force-overwrite -force-downgrade /usr/lib/enigma2/python/Plugins/Extensions/TMBD/enigma2-plugin-extensions-yttrailer_2.0_all.ipk"
			self.session.open(Console, _("Install YTTrailer..."), [cmd])

	def searchYttrailer(self):
		if self.curResult:
			current = self["menu"].l.getCurrentSelection()
			if current:
				namedetals = self['menu'].l.getCurrentSelection()[0]
				namedetals = namedetals[:-7]
				self.session.open(tmbdYTTrailer.TmbdYTTrailerList, namedetals)

	def workingFinished(self, callback=None):
		self.working = False

	def openKeyBoard(self):
		global eventname
		self.session.openWithCallback(
			self.gotSearchString,
			InputBox,
			title = _("Edit text to search for"), text=eventname, visible_width = 40, maxSize=False, type=Input.TEXT)

	def openVirtualKeyBoard(self):
		if config.plugins.tmbd.virtual_text.value == "0":
			self.session.openWithCallback(
				self.gotSearchString,
				VirtualKeyBoard,
				title = _("Enter text to search for")
			)
		else:
			global eventname
			self.session.openWithCallback(
				self.gotSearchString,
				VirtualKeyBoard,
				title = _("Edit text to search for"),
				text=eventname
			)

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.gotSearchString,
			TMBDChannelSelection
		)

	def gotSearchString(self, ret = None):
		if self.tmdb3 is None:
			return
		if ret:
			global total
			self.eventName = ret
			self.Page = 0
			self.resultlist = []
			self["menu"].hide()
			self["ratinglabel"].hide()
			self["castlabel"].hide()
			self["detailslabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self.removCovers()
			total = ""
			self["detailslabel"].setText("")
			self["statusbar"].setText("")
			self.noExit = False
			self.curResult = False
			self["key_yellow"].setText("")
			self["key_green"].setText("")
			if config.plugins.tmbd.test_connect.value:
				self.TestConnection()
			else:
				self.getTMBD()

	def getTMBD(self):
		global eventname, total
		total = ""
		results = ""
		self.resetLabels()
		if self.tmdb3 is None:
			return
		if not self.eventName:
			s = self.session.nav.getCurrentService()
			info = s and s.info()
			event = info and info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()
		if self.eventName:
			title = self.eventName.split("(")[0].strip()
			try:
				results = self.tmdb3.searchMovie(title)
			except:
				results = []
			if len(results) == 0:
				self["statusbar"].setText(_("Nothing found for: %s") % (self.eventName))
				self["title"].setText("")
				eventname = self.eventName
				self.curResult = False
				return False
			self.resultlist = []
			for searchResult in results:
				try:
					name = searchResult.title.encode('utf-8', 'ignore')
					self.resultlist.append((name, searchResult))
					total = len(results)
					if len(results) > 0:
						self["statusbar"].setText(_("Total results: %s") % (total))
					eventname = self.eventName
					self.curResult = True
				except:
					self.resultlist = []
			self.showMenu()
			self["menu"].setList(self.resultlist)
		else:
			self["title"].setText(_("Enter or choose event for search ..."))


	def TMBDPoster(self):
		if not self.curResult:
			self.removCovers()
		if fileExists("/tmp/preview.jpg"):
			jpg_file = "/tmp/preview.jpg"
		else:
			jpg_file = resolveFilename(SCOPE_PLUGINS, "Extensions/TMBD/picon_default.png")
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(jpg_file)

	def textNo(self, text):
		try:
			if text == None or text == "0":
				return ''
			else:
				return _("/ Duration: ") + text + _(" min.")
		except:
			return ''

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None and self.curResult:
			self["poster"].instance.setPixmap(ptr.__deref__())
			self["poster"].show()
		else:
			self["poster"].hide()

	def createSummary(self):
		#return TMBDLCDScreen
		pass

#class TMBDLCDScreen(Screen):
#	skin = """
#	<screen position="0,0" size="132,64" title="TMBD Plugin">
#		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
#		<widget source="parent.title" render="Label" position="6,26" size="120,34" font="Regular;14"/>
#	</screen>"""

#	def __init__(self, session, parent):
#		Screen.__init__(self, session, parent)
#		self["headline"] = Label(_("Search in themoviedb.org"))

class KinopoiskConfiguration(Screen):
	skin = """
	<screen position="center,center" size="450,100" title="Kinopoisk Configuration" >
		<widget name="menu" position="0,10" size="450,90" scrollbarMode="showOnDemand" />
	</screen>"""
	
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.menu = args
		self.setTitle(_("Choose action:"))
		list = []
		#list.append((_("Install packages library lmxl"), "lmxl"))
		list.append((_("Option for all images"), "all"))
		list.append((_("Option only python 2.7 images"), "new"))
		self["menu"] = MenuList(list)
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.run, "cancel": self.close}, -1)
	
	def run(self):
		returnValue = self["menu"].l.getCurrentSelection()[1]
		if returnValue is not None:
			if returnValue is "lmxl":
				cmd = "opkg install /usr/lib/enigma2/python/Plugins/Extensions/TMBD/lmxl/*.ipk  && echo 'If ok, to apply the changes required restart GUI!' "
				self.session.open(Console,_("Install packages library lmxl"),[cmd])
			elif returnValue is "all":
				cmd = "cp /usr/lib/enigma2/python/Plugins/Extensions/TMBD/profile/kinopoiskall.py /usr/lib/enigma2/python/Plugins/Extensions/TMBD/kinopoisk.py && echo 'Done...\nTo apply the changes required restart GUI!' "
				self.session.open(Console,_("Option for all images"),[cmd])
			elif returnValue is "new": 
				cmd = "cp /usr/lib/enigma2/python/Plugins/Extensions/TMBD/profile/kinopoisklmxl.py /usr/lib/enigma2/python/Plugins/Extensions/TMBD/kinopoisk.py && echo 'Done...\nTo apply the changes required restart GUI!' "
				self.session.open(Console,_("Option only python 2.7 images"),[cmd])

class TMBDSettings(Screen, ConfigListScreen):
	skin = """<screen position="center,center" size="740,485" title="TMBDSettings" backgroundColor="#31000000" >
		<widget name="config" position="10,10" size="725,428" zPosition="1" transparent="0" backgroundColor="#31000000" scrollbarMode="showOnDemand" />
		<widget name="key_red" position="10,460" zPosition="2" size="235,25" halign="center" font="Regular;22" transparent="1" foregroundColor="red"  />
		<widget name="key_green" position="485,460" zPosition="2" size="235,25" halign="center" font="Regular;22" transparent="1" foregroundColor="green" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position="10,450" size="235,44" zPosition="1" alphatest="on" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="485,450" size="235,44" zPosition="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.setTitle(_("Settings TMBD Details Plugin...") + " " + plugin_version)
		self['key_red'] = Button(_('Cancel'))
		self['key_green'] = Button(_('Save'))
		self['actions'] = ActionMap(['SetupActions',
		    'ColorActions'], {'green': self.save,
	            'ok': self.keyOK,
	            'red': self.exit,
	            'cancel': self.exit}, -2)

		ConfigListScreen.__init__(self, [])
		self.prev_ext_menu = config.plugins.tmbd.add_ext_menu.value
		self.initConfig()
		self.createSetup()
		
	def initConfig(self):
		def getPrevValues(section):
			res = { }
			for (key,val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res
		self.TM_BD = config.plugins.tmbd
		self.prev_values = getPrevValues(self.TM_BD)
		self.cfg_addmenu = getConfigListEntry(_('Show \"TMBD Details: current event\" in extensions menu'), config.plugins.tmbd.add_ext_menu)
		self.cfg_Event = getConfigListEntry(_("Event mode for search"), config.plugins.tmbd.ext_menu_event)
		self.cfg_noevent = getConfigListEntry(_("Open plugin if there is no event"), config.plugins.tmbd.no_event)
		self.cfg_locale = getConfigListEntry(_('Select the search language'), config.plugins.tmbd.locale)
		self.cfg_hotkey = getConfigListEntry(_('\"TMBD Details: current event\" quick button'), config.plugins.tmbd.hotkey)
		self.cfg_menu_profile = getConfigListEntry(_('Choice profile in search'), config.plugins.tmbd.menu_profile)
		self.cfg_movielist_profile = getConfigListEntry(_('Profile movielist context menu'), config.plugins.tmbd.movielist_profile)
		self.cfg_kinopoisk_data = getConfigListEntry(_('Data processing method for Kinopoisk.ru'), config.plugins.tmbd.kinopoisk_data)
		self.cfg_yt_setup = getConfigListEntry(_('Open yt-trailer setup'), config.plugins.tmbd.yt_setup)
		self.cfg_yt_event_menu = getConfigListEntry(_('Add yt-trailer to context menu EPG'), config.plugins.tmbd.yt_event_menu)
		self.cfg_add_tmbd_to_nstreamvod = getConfigListEntry(_('Add \"search in TMBD\" Info/EPG Button to nStreamVOD'), config.plugins.tmbd.add_tmbd_to_nstreamvod)
		self.cfg_add_vcs_to_nstreamvod = getConfigListEntry(_('Add \"open plugin VCS\" Info/EPG Button to nStreamVOD'), config.plugins.tmbd.add_vcs_to_nstreamvod)

	def createSetup(self):
		list = []
		list.append(getConfigListEntry(_('Choice database to search'), config.plugins.tmbd.profile))
		if config.plugins.tmbd.profile.value == "0":
			list.append(self.cfg_locale)
		else:
			list.append(self.cfg_kinopoisk_data)
		list.append(getConfigListEntry(_('Select your skins'), config.plugins.tmbd.skins))
		#list.append(getConfigListEntry(_('Add \"Lookup in TMBD\" Info Button to single-EPG'), config.plugins.tmbd.add_tmbd_to_epg))
		#list.append(getConfigListEntry(_('Add \"Lookup in TMBD\" Info Button to multi-EPG'), config.plugins.tmbd.add_tmbd_to_multi))
		#list.append(getConfigListEntry(_('Add \"Lookup in TMBD\" Info Button to GraphMultiEpg'), config.plugins.tmbd.add_tmbd_to_graph))
		if epg_furtherOptions:
			list.append(getConfigListEntry(_('Add \"Search event in TMBD\"  to event menu'), config.plugins.tmbd.show_in_furtheroptionsmenu))
		list.append(getConfigListEntry(_('Open VirtualKeyBoard'), config.plugins.tmbd.virtual_text))
		list.append(getConfigListEntry(_('Show plugin in channel selection context menu'), config.plugins.tmbd.menu))
		if config.plugins.tmbd.menu.value:
			list.append(self.cfg_menu_profile)
		list.append(self.cfg_hotkey)
		list.append(self.cfg_addmenu)
		if config.plugins.tmbd.add_ext_menu.value or config.plugins.tmbd.hotkey.value != "none":
			list.append(self.cfg_Event)
			list.append(self.cfg_noevent)
		list.append(self.cfg_movielist_profile)
		list.append(getConfigListEntry(_('Check status Internet'), config.plugins.tmbd.test_connect))
		list.append(getConfigListEntry(_('Show info for all types of movies'), config.plugins.tmbd.new_movieselect))
		list.append(getConfigListEntry(_('Close plugin EXIT Button'), config.plugins.tmbd.exit_key))
		list.append(self.cfg_yt_setup)
		list.append(self.cfg_yt_event_menu)
		if config.plugins.tmbd.yt_event_menu.value != "0":
			list.append(getConfigListEntry(_('Behavior after searching trailers'), config.plugins.tmbd.yt_start))
		list.append(getConfigListEntry(_('Select folder for covers'), config.plugins.tmbd.cover_dir))
		#if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/nStreamVOD/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/nStreamVOD/plugin.pyc"):
		#	list.append(self.cfg_add_tmbd_to_nstreamvod)
		#	if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VCS/plugin.pyo") and fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VCS/VCS.pyo"):
		#		list.append(self.cfg_add_vcs_to_nstreamvod)
		#	else:
		#		config.plugins.tmbd.add_vcs_to_nstreamvod.value = False
		self["config"].list = list
		self["config"].l.setList(list)

	def keyOK(self):
		ConfigListScreen.keyOK(self)
		sel = self["config"].getCurrent()[1]
		if sel == config.plugins.tmbd.kinopoisk_data:
			self.session.open(KinopoiskConfiguration)
		if sel == config.plugins.tmbd.yt_setup:
			self.session.open(tmbdYTTrailer.TmbdYTTrailerSetup)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def save(self):
		dir = self.TM_BD.cover_dir.value
		if not dir.endswith("/"):
			self.TM_BD.cover_dir.value = dir + "/"
		if self.TM_BD.cover_dir.value == "" or self.TM_BD.cover_dir.value == "/":
			self.TM_BD.cover_dir.value = "/media/hdd/"
		self.TM_BD.save()
		if self.prev_ext_menu != config.plugins.tmbd.add_ext_menu.value:
			plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

	def exit(self):
		def setPrevValues(section, values):
			for (key,val) in section.content.items.items():
				value = values.get(key, None)
				if value is not None:
					if isinstance(val, ConfigSubsection):
						setPrevValues(val, value)
					else:
						val.value = value
		setPrevValues(self.TM_BD, self.prev_values)
		self.save()

class KinoRu(Screen):
	skin_hd1 = """
		<screen name="KinoRu" position="90,90" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="740,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="770,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="770,10"  size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" halign="left" name="ratinglabel" foregroundColor="#00f0b400" position="770,34" size="210,23" transparent="1" />
		<widget font="Regular;20" name="voteslabel" halign="left" position="770,57" size="330,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,60" size="285,398" />
		<widget name="menu" position="20,270" foregroundColor="#00f0b400" scrollbarMode="showOnDemand" size="1100,200" zPosition="1"  selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,230" size="570,23" font="Regular;20" transparent="1" />  
		<widget font="Regular;20" name="castlabel" position="320,350" size="760,160" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="320,80" size="760,285" transparent="1" />
		<widget font="Regular;22" name="titlelabel" position="380,85" foregroundColor="#00f0b400" size="700,340" transparent="1" />
		<widget font="Regular;18" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<widget name="kino" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/kino_ru.png" transparent="1" position="30,90" size="350,300" zPosition="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""

	skin_hd = """
		<screen name="KinoRu" position="90,90" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="740,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="770,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="770,10"  size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" halign="left" name="ratinglabel" foregroundColor="#00f0b400" position="770,34" size="210,23" transparent="1" />
		<widget font="Regular;20" name="voteslabel" halign="left" position="770,57" size="330,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,80" size="110,170" />
		<widget name="menu" position="20,270" foregroundColor="#00f0b400" scrollbarMode="showOnDemand" size="1100,200" zPosition="1"  selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,230" size="570,23" font="Regular;20" transparent="1" />  
		<widget font="Regular;20" name="castlabel" position="20,295" size="1064,195" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="164,77" size="920,220" transparent="1" />
		<widget font="Regular;22" name="titlelabel" position="380,85" foregroundColor="#00f0b400" size="700,340" transparent="1" />
		<widget font="Regular;18" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<widget name="kino" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/kino_ru.png" transparent="1" position="30,90" size="350,300" zPosition="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""

	skin_fullhd1 = """
		<screen name="KinoRu" position="center,center" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="740,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="770,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="770,10"  size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" halign="left" name="ratinglabel" foregroundColor="#00f0b400" position="770,34" size="210,23" transparent="1" />
		<widget font="Regular;20" name="voteslabel" halign="left" position="770,57" size="330,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,60" size="285,398" />
		<widget name="menu" position="20,270" foregroundColor="#00f0b400" scrollbarMode="showOnDemand" size="1100,200" zPosition="1"  selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,230" size="570,23" font="Regular;20" transparent="1" />  
		<widget font="Regular;20" name="castlabel" position="320,350" size="760,160" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="320,80" size="760,285" transparent="1" />
		<widget font="Regular;22" name="titlelabel" position="380,85" foregroundColor="#00f0b400" size="700,340" transparent="1" />
		<widget font="Regular;18" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<widget name="kino" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/kino_ru.png" transparent="1" position="30,90" size="350,300" zPosition="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""

	skin_fullhd = """
		<screen name="KinoRu" position="center,center" size="1100,570" title="TMBD Details Plugin">
		<eLabel backgroundColor="#00bbbbbb" position="0,0" size="1100,2" />
		<widget font="Regular;22" name="title" position="20,20" size="740,28" transparent="1" valign="center" />
		<widget alphatest="blend" name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="770,10" size="210,21" zPosition="2" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" position="770,10"  size="210,21" transparent="1" zPosition="3" />
		<widget font="Regular;20" halign="left" name="ratinglabel" foregroundColor="#00f0b400" position="770,34" size="210,23" transparent="1" />
		<widget font="Regular;20" name="voteslabel" halign="left" position="770,57" size="330,23" foregroundColor="#00f0b400" transparent="1" />
		<widget alphatest="blend" name="poster" position="30,80" size="110,170" />
		<widget name="menu" position="20,270" foregroundColor="#00f0b400" scrollbarMode="showOnDemand" size="1100,200" zPosition="1"  selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/button1080x25.png" />
		<widget name="detailslabel" position="325,230" size="570,23" font="Regular;20" transparent="1" />  
		<widget font="Regular;20" name="castlabel" position="20,295" size="1064,195" transparent="1" />
		<widget font="Regular;20" name="extralabel" position="164,77" size="920,220" transparent="1" />
		<widget font="Regular;22" name="titlelabel" position="380,85" foregroundColor="#00f0b400" size="700,340" transparent="1" />
		<widget font="Regular;18" name="statusbar" position="10,490" size="1080,20" transparent="1" />
		<widget name="kino" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/kino_ru.png" transparent="1" position="30,90" size="350,300" zPosition="1" />
		<eLabel backgroundColor="#00bbbbbb" position="0,518" size="1100,2" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/red25.png" position=" 20,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/green25.png" position="290,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/yellow25.png" position="560,532" size="250,38" zPosition="1" />
		<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/ig/blue25.png" position="830,532" size="250,38" zPosition="1" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="1048,5" zPosition="1" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="1048,35" zPosition="1" size="35,25" alphatest="on" />
		<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="center" name="key_red" position=" 20,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="center" name="key_green" position="290,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="center" name="key_yellow" position="560,536" size="250,38" transparent="1" valign="center" zPosition="2" />
		<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="center" name="key_blue" position="830,536" size="250,38" transparent="1" valign="center" zPosition="2" />
	</screen>"""

	skin_sd = """
		<screen name="KinoRu" position="center,center" size="600,420" title="TMBD Details Plugin" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="565,5" zPosition="0" size="35,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="565,33" zPosition="1" size="35,25" alphatest="on" />
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
		<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;18" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
		<widget name="title" position="10,40" size="330,45" valign="center" font="Regular;19"/>
		<widget name="kino" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/kino_smail.png" transparent="1" position="10,110" size="110,170" zPosition="1" />
		<widget font="Regular;20" name="titlelabel" position="140,90" size="440,140" transparent="1" />
		<widget name="extralabel" position="105,90" size="485,140" font="Regular;18" />
		<widget name="castlabel" position="10,235" size="580,155" font="Regular;18"  zPosition="3"/>
		<widget name="ratinglabel" position="340,62" size="250,20" halign="center" font="Regular;18" foregroundColor="#f0b400"/>
		<widget name="statusbar" position="10,404" size="580,16" font="Regular;16" foregroundColor="#cccccc" />
		<widget font="Regular;16" halign="center" name="voteslabel" foregroundColor="#00f0b400" position="380,404" size="210,16" transparent="1" />
		<widget name="poster" position="4,90" size="96,140" alphatest="on" />
		<widget name="menu"  position="10,235" size="580,155" zPosition="2" scrollbarMode="showOnDemand" />
		<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_empty.png" position="340,40" zPosition="0" size="210,21" transparent="1" alphatest="on" />
	<widget name="stars" position="340,40" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TMBD/starsbar_filled.png" transparent="1" />
	</screen>"""  

	def __init__(self, session, eventName, callbackNeeded=False, movielist=False):
		Screen.__init__(self, session)
		self.skin = self.chooseSkin()
		self.eventName = eventName
		self.curResult = False
		self.noExit = False
		self.curPoster = False
		self.curInfos = False
		self.curPoster = False
		self.rating = None
		self.votes = None
		self.countrie = None
		self.year = None
		self.runtimes = None
		self.genres = None
		self.director = None
		self.cast = None
		self.age = None
		self.duplicated = None
		self.plot = None
		self.onShow.append(self.selectionChanged)
		self.movielist = movielist
		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""
		self["kino"] = Pixmap()
		self["kino"].show()
		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1
		self.working = False
		self["title"] = Label("")
		self["title"].setText(_("Search in kinopoisk.ru ,please wait ..."))
		self["detailslabel"] = ScrollLabel("")
		self["castlabel"] = ScrollLabel("")
		self["extralabel"] = ScrollLabel("")
		self["statusbar"] = Label("")
		self["ratinglabel"] = Label("")
		self["titlelabel"] = ScrollLabel("")
		self["titlelabel"].hide()
		self["voteslabel"] = Label("")
		self.resultlist = []
		self["menu"] = MenuList(self.resultlist)
		self["menu"].hide()
		self["menu"].onSelectionChanged.append(self.selectionChanged)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Manual input"))
		self.Page = 0
		self.working = False
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.KinoRuPoster)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
		{
			"ok": self.showExtras,
			"cancel": self.exit2,
			"down": self.pageDown,
			"up": self.pageUp,
			"left": self.scrollLabelPageUp,
			"right": self.scrollLabelPageDown,
			"red": self.exit,
			"green": self.searchYttrailer2,
			"yellow": self.showExtras,
			"blue": self.openVirtualKeyBoard,
			"contextMenu": self.contextMenuPressed,
			"showEventInfo": self.aboutAutor
		}, -1)

		self.setTitle(_("Profile: kinopoisk.ru"))
		self.removCovers()
		self.testThread = None
		self.testTime = 2.0		# 1 seconds
		self.testHost = "www.kinopoisk.ru"
		self.testPort = 80		# www port
		if config.plugins.tmbd.test_connect.value:
			self.TestConnection()
		else:
			self.getKinoRu()

	def chooseSkin(self):
		try:
			screenWidth = getDesktop(0).size().width()
		except:
			screenWidth = 720
		if screenWidth >= 1920: #TODO!!!
			if config.plugins.tmbd.skins.value == "0":
				return KinoRu.skin_fullhd
			if config.plugins.tmbd.skins.value == "1":
				return KinoRu.skin_fullhd1
		elif screenWidth >= 1280:
			if config.plugins.tmbd.skins.value == "0":
				return KinoRu.skin_hd
			if config.plugins.tmbd.skins.value == "1":
				return KinoRu.skin_hd1
		else:
			return KinoRu.skin_sd

	def TestConnection(self):
		self.testThread = Thread(target=self.test)
		self.testThread.start()

	def get_iface_list(self):
		names = array.array('B', '\0' * BYTES)
		sck = socket(AF_INET, SOCK_DGRAM)
		bytelen = struct.unpack('iL', fcntl.ioctl(sck.fileno(), SIOCGIFCONF, struct.pack('iL', BYTES, names.buffer_info()[0])))[0]
		sck.close()
		namestr = names.tostring()
		return [namestr[i:i+32].split('\0', 1)[0] for i in range(0, bytelen, 32)]

	def test(self):
		global testOK
		link = "down"
		for iface in self.get_iface_list():
			if "lo" in iface: continue
			if os.path.exists("/sys/class/net/%s/operstate"%(iface)):
				fd = open("/sys/class/net/%s/operstate"%(iface), "r")
				link = fd.read().strip()
				fd.close()
			if link != "down": break
		if link != "down":
			s = socket(AF_INET, SOCK_STREAM)
			s.settimeout(self.testTime)
			try:
				testOK = not bool(s.connect_ex((self.testHost, self.testPort)))
			except:
				testOK = None
			if not testOK:
				print 'Conection failed'
				self.resetLabels()
				self["statusbar"].setText(_("No connect to kinopoisk.ru..."))
				s.close()
				self["title"].setText("")
				return
			else:
				s.shutdown(SHUT_RDWR)
				s.close()
				self.pauseTimer = eTimer()
				self.pauseTimer.callback.append(self.getKinoRu)
				self.pauseTimer.start(1500, True)
		else:
			testOK = None
			self.resetLabels()
			self["statusbar"].setText(_("Not found network connection..."))
			self["title"].setText("")
			return

	def exit(self):
		self.close()

	def exit2(self):
		if config.plugins.tmbd.exit_key.value == "1":
			self.session.openWithCallback(self.exitConfirmed, MessageBox, _("Close plugin?"), MessageBox.TYPE_YESNO)
		else:
			self.exit()

	def exitConfirmed(self, answer):
		if answer:
			self.close()

	def aboutAutor(self):
		self.session.open(MessageBox, _("Kinopoisk.ru\nDeveloper: Dima73(Dimitrij) 2012/2014"), MessageBox.TYPE_INFO)

	def removCovers(self):
		if os.path.exists('/tmp/preview.jpg'):
				try:
					os.remove('/tmp/preview.jpg')
				except:
					pass

	def resetLabels(self):
		try:
			self["detailslabel"].setText("")
			self["ratinglabel"].setText("")
			self["title"].setText(_("Search in kinopoisk.ru ,please wait ..."))
			self["castlabel"].setText("")
			self["titlelabel"].setText("")
			self["extralabel"].setText("")
			self["voteslabel"].setText("")
			self["key_green"].setText("")
		except:
			pass
		self.ratingstars = -1
		self.curPoster = False
		self.rating = None
		self.votes = None
		self.countrie = None
		self.year = None
		self.runtimes = None
		self.genres = None
		self.director = None
		self.cast = None
		self.age = None
		self.duplicated = None
		self.plot = None
		self.curInfos = False

	def pageUp(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
			self["titlelabel"].pageUp()
		if self.Page == 1:
			self["castlabel"].pageUp()

	def pageDown(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
			self["titlelabel"].pageDown()
		if self.Page == 1:
			self["castlabel"].pageDown()

	def scrollLabelPageUp(self):
		self["extralabel"].pageUp()

	def scrollLabelPageDown(self):
		self["extralabel"].pageDown()

	def showMenu(self):
		global eventname, total
		self.noExit = False
		if self.curResult:
			self["menu"].show()
			self["kino"].show()
			self["titlelabel"].show()
			self["extralabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self["castlabel"].hide()
			self["ratinglabel"].setText("")
			self["extralabel"].setText("")
			self.ratingstars = -1
			self.curPoster = False
			self.curInfos = False
			self.rating = None
			self.votes = None
			self.countrie = None
			self.year = None
			self.runtimes = None
			self.genres = None
			self.director = None
			self.cast = None
			self.age = None
			self.duplicated = None
			self.plot = None
			self["castlabel"].setText("")
			self["castlabel"].setText("")
			self["voteslabel"].setText("")
			self["title"].setText(_("Search results for: %s") % (eventname))
			if total > 1:
				self["detailslabel"].setText(_("Please select the matching entry:"))
				self["detailslabel"].show()
			self["key_blue"].setText(_("Manual input"))
			if self.movielist:
				if self.resultlist:
					self["key_green"].setText(_("Search Trailer"))
			else:
				self["key_green"].setText(_("Search Trailer"))
			self["key_yellow"].setText(_("Show movie details"))
			self.working = True

	def showExtras(self):
		if self.curResult:
			if not self.noExit:
				self.Page = 1
				self.noExit = True
				self["menu"].hide()
				self["detailslabel"].hide()
				self["extralabel"].show()
				self["castlabel"].show()
				self["titlelabel"].hide()
				self["key_yellow"].setText("")
				self.showExtras2()
			else:
				self.Page = 0
				self.noExit = False
				self.showMenu()

	def showExtras2(self):
		if self.resultlist:
			sel = self['menu'].getCurrent()
			if sel:
				try:
					namedetals = sel.split(',')[0]
				except:
					namedetals = sel[0]
				id = None
				try:
					num = sel[1]
					if num.find("id:") != -1:
						id = num[4:]
					else:
						id = None
				except:
					id = None
				if id is None:
					try:
						id = sel.split('id:')[1]
					except:
						id = None
				if id is not None and id != 'n\a':
					if id != 'n\x07':
						try:
							film_data = kinopoisk.search_data(id)
						except:
							self.Page = 0
							self.noExit = False
							self.showMenu()
							return -1
						self["key_yellow"].setText(_("Show search results"))
						self["title"].setText(_("Details for: %s") % (namedetals))
						self.removCovers()
						self.refreshTimer.start(100, True)
						try:
							rating = film_data['user_rating'].encode("utf-8")
						except:
							rating = ''
						Ratingtext = ''
						if rating != '':
							Ratingtext = _("User Rating") + ": " + rating + " / 10"
							self.ratingstars = int(10*round(float(rating.replace(',','.')),1))
							self["stars"].show()
							self["stars"].setValue(self.ratingstars)
							self["starsbg"].show()
							self.rating = rating
						self["ratinglabel"].setText(Ratingtext)
						try:
							votes = film_data['rating_count'].encode("utf-8")
						except:
							votes = ''
						Votestext = ''
						if votes != '':
							Votestext = _("Votes") + ": " + votes + _(" times")
							self.votes = votes
						self["voteslabel"].setText(Votestext)
						Extratext = ""
						Extratext2 = ""
						try:
							countrie = film_data['countries'].encode("utf-8")
						except:
							countrie = ''
						if countrie != '':
							Extratext2 = "%s: %s\n" % (_("Country"), countrie)
							self.countrie = countrie
						try:
							year = film_data['year'].encode("utf-8")
						except:
							year = ''
						if year != '':
							Extratext2 += "%s: %s\n" % (_("Appeared"), year)
							self.year = year
						try:
							runtime = film_data['runtime'].encode("utf-8")
						except:
							runtime = ''
						if runtime != '' and runtime != '-':
							runtimes = runtime + _(" min.")
							Extratext2 += "%s: %s\n" % (_("Duration"), runtimes)
							self.runtimes = runtimes
						try:
							genres = film_data['genre'].encode("utf-8")
						except:
							genres = ''
						if genres != '':
							Extratext2 += "%s: %s\n" % (_("Genre"), genres)
							self.genres = genres
						try:
							director = film_data['directors'].encode("utf-8")
						except:
							director = ''
						if director != '':
							Extratext2 += "%s: %s\n" % (_("Director"), director)
							self.director = director
						try:
							cast = film_data['cast'].encode("utf-8")
						except:
							cast = ''
						if cast != '':
							Extratext = "%s: %s\n" % (_("Actors"), cast)
							self.cast = cast
						try:
							age = film_data['movie_rating'].encode("utf-8")
						except:
							age = ''
						if age != '':
							Extratext += "%s: %s\n" % (_("Age"), age)
							self.age = age
						try:
							duplicated = film_data['duplicate'].encode("utf-8")
						except:
							duplicated = ''
						if duplicated != '':
							#duplicated = duplicated[:-1]
							Extratext += "%s: %s\n" % (_("Roles duplicated"), duplicated)
							self.duplicated = duplicated
						self["extralabel"].setText("%s%s" % (Extratext2, Extratext))
						try:
							plot = film_data['plot'].encode("utf-8")
						except:
							plot = ''
						if plot != '':
							self["castlabel"].setText("%s" % (plot))
							self.plot = plot
						if Extratext2 != '' or Extratext != '':
							self.search_poster(id)
							if self.movielist:
								self["key_green"].setText(_("Save info / poster"))
								self.curInfos = True

	def search_poster(self, id):
		if id:
			if id.endswith("end"):
				id = id[:-3]
			#url = 'http://st.kinopoisk.ru/images/film_big/%s.jpg' % (id)
			url = 'http://st.kinopoisk.ru/images/film/%s.jpg' % (id)
			user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.53.11 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10'
			req = urllib2.Request(url, headers = {'User-agent': user_agent, 'Accept': 'text/html'})
			#req = urllib2.Request(url, headers={"Accept" : "text/html"})
			#req.add_header('User-agent',user_agent)
			try:
				res = urllib2.urlopen(req)
			except:
				print 'The server couldn\'t fulfill the request.'
				res = None
			if res != None:
				page = res.read()
				file = open('/tmp/preview.jpg','w')
				file.write(page)
				file.close()
				self["kino"].hide()
				self.curPoster = True
				self["poster"].show()
			
	def removmenu(self):
		list = [
			(_("Current poster and info"), self.removcurrent),
			(_("Only current poster"), self.removcurrentposter),
			(_("Only current info"), self.removcurrentinfo),
			(_("All posters for movie"), self.removresult),
		]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
			title= _("What exactly do you want to delete?"),
		)	

	def contextMenuPressed(self):
		if self.movielist:
			list = [
				(_("Text editing"), self.openKeyBoard),
				(_("Select from Favourites"), self.openChannelSelection),
				(_("Search Trailer"), self.searchYttrailer3),
				(_("Remove poster / info"), self.removmenu),
				(_("Settings"), self.Menu2),
			]
		else:
			list = [
				(_("Text editing"), self.openKeyBoard),
				(_("Select from Favourites"), self.openChannelSelection),
				(_("Settings"), self.Menu2),
			]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
			title= _("Select action:"),
		)

	def Menu2(self):
		self.session.openWithCallback(self.workingFinished, TMBDSettings)

	def saveresult(self):
		global name
		list = [
			(_("Yes"), self.savePosterInfo),
			(_("Yes,but write new meta-file"), self.writeMeta),
			(_("Only poster"), self.savePoster),
			(_("No"), self.exitChoice),
		]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title= _("Save poster and info for:\n %s ?") % (name),
			list = list,
		)

	def exitChoice(self):
		self.close()
		
	def savePoster(self):
		global name
		import os
		import shutil
		if self.curResult and self.curInfos and self.curPoster:
			dir = config.plugins.tmbd.cover_dir.value + 'covers'
			if not fileExists(dir):
				try:
					os.makedirs(dir)
				except OSError:
					pass
			if fileExists(dir):
				try:
					if fileExists("/tmp/preview.jpg"):
						shutil.copy2("/tmp/preview.jpg", dir + "/" + name + ".jpg")
						self.session.open(MessageBox, _("Poster %s saved!") % (name), MessageBox.TYPE_INFO, timeout=2)
				except OSError:
					pass

	def savePosterInfo(self):
		global name
		import os
		import shutil
		if self.curResult and self.curInfos:
			self.savedescrip()
		dir = config.plugins.tmbd.cover_dir.value + 'covers'
		if not fileExists(dir):
			try:
				os.makedirs(dir)
			except OSError:
				pass
		if fileExists(dir):
			try:
				if fileExists("/tmp/preview.jpg") and self.curPoster:
					shutil.copy2("/tmp/preview.jpg", dir + "/" + name + ".jpg")
					self.session.open(MessageBox, _("Poster %s saved!") % (name), MessageBox.TYPE_INFO, timeout=2)
			except OSError:
				pass

	def writeMeta(self):
		if self.curResult and self.curInfos:
			global name, movie2, eventname
			Extratext2 = ""
			namedetals2 = ""
			if len(movie2):
					TSFILE = movie2
			else:
				return
			current = self["menu"].l.getCurrentSelection()
			if current:
				try:
					namedetals2 = current.split(',')[0]
				except:
					namedetals2 = current[0]
				namedetals2 = namedetals2[:-6]
				namedetals2 = namedetals2.replace('\n','')
				if movie2.endswith(".ts"):
					name = namedetals2
				else:
					Extratext2 = "%s" % ( namedetals2)
				if self.genres:
					genre = self.genres
					genre = genre.replace('...', '')
					Extratext2 += " %s /" % (genre)
				if self.countrie:
					Extratext2 += " %s /" % (self.countrie)
				if self.cast:
					Extratext2 += " %s" % (self.cast)
				metaParser = MetaParser();
				metaParser.name = namedetals2
				metaParser.description = Extratext2;
				if os.path.exists(TSFILE + '.meta') and movie2.endswith(".ts"):
					readmetafile = open("%s.meta"%(movie2), "r")
					linecnt = 0
					line = readmetafile.readline()
					if line:
						line = line.strip()
						if linecnt == 0:
							metaParser.ref = eServiceReference(line)
					else:
						metaParser.ref = eServiceReference('1:0:0:0:0:0:0:0:0:0:')
					readmetafile.close()
				else:
					metaParser.ref = eServiceReference('1:0:0:0:0:0:0:0:0:0:')
				metaParser.time_create = getctime(TSFILE);
				metaParser.tags = '';
				metaParser.length = 0;
				metaParser.filesize = fileSize(TSFILE);
				metaParser.service_data = '';
				metaParser.data_ok = 1;
				metaParser.updateMeta(TSFILE);
				self.session.open(MessageBox, _("Write to new meta-file for:\n") + "%s" % (TSFILE), MessageBox.TYPE_INFO, timeout=3)
				self.timer = eTimer()
				self.timer.callback.append(self.savePosterInfo)
				self.timer.start(1500, True)

	def savedescrip(self):
		global name, movie2
		descrip = ""
		Extratext = ""
		namedetals = ""
		if len(movie2):
			EITFILE = movie2[:-2] + 'eit'
		else:
			return
		current = self["menu"].l.getCurrentSelection()
		if current:
			try:
				namedetals = current.split(',')[0]
			except:
				namedetals = current[0]
			if self.countrie:
				Extratext = "%s %s\n" % (_("Country:"), self.countrie)
			if self.genres:
				Extratext += "%s %s\n" % (_("Genre:"), self.genres)
			if self.plot:
				descrip = " %s\n" % (self.plot)
			if self.runtimes:
				descrip += " %s /" % (self.runtimes)
			if self.age:
				descrip += " %s %s /" % (_("Age:"), self.age)
			if self.rating and self.votes:
				descrip += _(" User Rating: ") + self.rating + _(" (%s votes)\n") % (self.votes)
			if self.director:
				descrip += "%s: %s\n" % (_("Director"), self.director)
			if self.cast:
				descrip += " %s %s\n" % (_("Actors:"), self.cast)
			if self.duplicated:
				descrip += " %s %s\n" % (_("Roles duplicated:"), self.duplicated)
			Extratext = Extratext.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			Extratext = self.Cutext(Extratext)
			descrip = descrip.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			namedetals = namedetals.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-');
			sed = ShortEventDescriptor([]);
			sed.setIso639LanguageCode('rus');
			sed.setEventName(namedetals);
			sed.setText(Extratext);
			eed = ExtendedEventDescriptor([]);
			eed.setIso639LanguageCode('rus');
			eed.setText(descrip);
			newEvent = Event();
			newEvent.setShortEventDescriptor(sed);
			newEvent.setExtendedEventDescriptor(eed);
			ret = newEvent.saveToFile(EITFILE);
			self.session.open(MessageBox, _("Write event to new eit-file:\n") + "%s\n" % (EITFILE) + _("%d bytes") % (ret), MessageBox.TYPE_INFO, timeout=3)

	def Cutext(self, text):
		if text > 0:
			return text[:179]
		else:
			return text

	def removcurrent(self):
		global name
		self.session.openWithCallback(self.removcurrentConfirmed, MessageBox, _("Remove current poster and info for:\n%s ?") % (name), MessageBox.TYPE_YESNO)

	def removcurrentposter(self):
		global movie2, name
		if len(movie2):
			dir_cover = config.plugins.tmbd.cover_dir.value + 'covers/'
			if movie2.endswith(".ts"):
				if os.path.exists(movie2 + '.meta'):
					try:
						readmetafile = open("%s.meta"%(movie2), "r")
						name_cur = readmetafile.readline()[0:-1]
						name_cover = name_cur + '.jpg'
					except:
						name_cover = ""
					readmetafile.close()
				else:
					name_cover = name + '.jpg'
			else:
					name_cover = name + '.jpg'
			remove_jpg = dir_cover + name_cover
			if os.path.exists(remove_jpg):
				try:
					os.remove(remove_jpg)
					self.session.open(MessageBox, _("%s poster removed!") % (remove_jpg), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
		else:
			return

	def removcurrentinfo(self):
		global movie2, name
		if len(movie2):
			remove_eit = movie2[:-2] + 'eit'
			if os.path.exists(remove_eit):
				try:
					os.remove(remove_eit)
					self.session.open(MessageBox, _("%s eit-file removed!") % (remove_eit), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
			remove_meta = movie2 + '.meta'
			if os.path.exists(remove_meta):
				try:
					os.remove(remove_meta)
					self.session.open(MessageBox, _("%s meta-file removed!") % (remove_meta), MessageBox.TYPE_INFO, timeout=3)
				except:
					pass
		else:
			return

	def removcurrentConfirmed(self, confirmed):
		if not confirmed:
			return
		else:
			global movie2, name
			if len(movie2):
				dir_cover = config.plugins.tmbd.cover_dir.value + 'covers/'
				remove_eit = movie2[:-2] + 'eit'
				if os.path.exists(remove_eit):
					try:
						os.remove(remove_eit)
						self.session.open(MessageBox, _("%s eit-file removed!") % (remove_eit), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
				if movie2.endswith(".ts"):
					if os.path.exists(movie2 + '.meta'):
						try:
							readmetafile = open("%s.meta"%(movie2), "r")
							name_cur = readmetafile.readline()[0:-1]
							name_cover = name_cur + '.jpg'
						except:
							name_cover = ""
						readmetafile.close()
					else:
						name_cover = name + '.jpg'
				else:
					name_cover = name + '.jpg'
				remove_jpg = dir_cover + name_cover
				if os.path.exists(remove_jpg):
					try:
						os.remove(remove_jpg)
						self.session.open(MessageBox, _("%s poster removed!") % (remove_jpg), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
				remove_meta = movie2 + '.meta'
				if os.path.exists(remove_meta):
					try:
						os.remove(remove_meta)
						self.session.open(MessageBox, _("%s meta-file removed!") % (remove_meta), MessageBox.TYPE_INFO, timeout=3)
					except:
						pass
			else:
				return

	def removresult(self):
		self.session.openWithCallback(self.removresultConfirmed, MessageBox, _("Remove all posters?"), MessageBox.TYPE_YESNO)

	def removresultConfirmed(self, confirmed):
		import os
		import shutil
		if not confirmed:
			return
		else:
			dir = config.plugins.tmbd.cover_dir.value + 'covers'
			if fileExists(dir):
				try:
					shutil.rmtree(dir)
					self.session.open(MessageBox, _("All posters removed!"), MessageBox.TYPE_INFO, timeout=3)
				except OSError:
					pass

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def searchYttrailer3(self):
		self.searchYttrailer()

	def searchYttrailer2(self):
		if self.movielist and self.curResult and self.curInfos:
			self.saveresult()
		else:
			self.searchYttrailer()

	def yesNo(self, answer):
		if answer is True:
			self.yesInstall()

	def yesInstall(self):
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/TMBD/enigma2-plugin-extensions-yttrailer_2.0_all.ipk")):
			cmd = "opkg install -force-overwrite -force-downgrade /usr/lib/enigma2/python/Plugins/Extensions/TMBD/enigma2-plugin-extensions-yttrailer_2.0_all.ipk"
			self.session.open(Console, _("Install YTTrailer..."), [cmd])

	def searchYttrailer(self):
		if self.curResult:
			current = self["menu"].l.getCurrentSelection()
			if current:
				try:
					namedetals = current.split(',')[0]
				except:
					namedetals = current[0]
				namedetals = namedetals.replace('\xc2\xab', '"').replace('\xc2\xbb', '"').replace('\xe2\x80\xa6', '...').replace('\xe2\x80\x94', '-')
				namedetals = namedetals[:-6]
				self.session.open(tmbdYTTrailer.TmbdYTTrailerList, namedetals)

	def workingFinished(self, callback=None):
		self.working = False

	def openKeyBoard(self):
		global eventname
		self.session.openWithCallback(
			self.gotSearchString,
			InputBox,
			title = _("Edit text to search for"), text=eventname, visible_width = 40, maxSize=False, type=Input.TEXT)

	def openVirtualKeyBoard(self):
		if config.plugins.tmbd.virtual_text.value == "0":
			self.session.openWithCallback(
				self.gotSearchString,
				VirtualKeyBoard,
				title = _("Enter text to search for")
			)
		else:
			global eventname
			self.session.openWithCallback(
				self.gotSearchString,
				VirtualKeyBoard,
				title = _("Edit text to search for"),
				text=eventname
			)

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.gotSearchString,
			TMBDChannelSelection
		)

	def gotSearchString(self, ret = None):
		if ret:
			global total
			self.eventName = ret
			self.Page = 0
			self.resultlist = []
			self["menu"].hide()
			self.resetLabels()
			self["castlabel"].setText("")
			self["ratinglabel"].setText("")
			self["castlabel"].hide()
			self["extralabel"].setText("")
			self["voteslabel"].setText("")
			self["titlelabel"].setText("")
			self["detailslabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self.removCovers()
			total = 0
			self["detailslabel"].setText("")
			self["statusbar"].setText("")
			self.noExit = False
			self.curResult = False
			self.curPoster = False
			self.curInfos = False
			self.rating = None
			self.votes = None
			self.countrie = None
			self.year = None
			self.runtimes = None
			self.genres = None
			self.director = None
			self.cast = None
			self.age = None
			self.duplicated = None
			self.plot = None
			self["key_yellow"].setText("")
			self["key_green"].setText("")
			self["kino"].show()
			self["title"].setText(_("Search in kinopoisk.ru ,please wait ..."))
			if config.plugins.tmbd.test_connect.value:
				self.TestConnection()
			else:
				self.getKinoRu()

	def getKinoRu(self):
		global eventname, total
		total = ""
		self.resetLabels()
		if not self.eventName:
			s = self.session.nav.getCurrentService()
			info = s and s.info()
			event = info and info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()
		if self.eventName:
			title = self.eventName.split("(")[0].strip()
			title = cutName(title)
			try:
				results = kinopoisk.search_title(title)
			except:
				results = []
			if results is None:
				self["statusbar"].setText("")
				self["title"].setText("")
				eventname = self.eventName
				self.curResult = False
				try:
					self.session.open(MessageBox, _("Library lmxl is not installed!\nTry to install the library again or change the method of processing data in the settings menu."), MessageBox.TYPE_ERROR)
				except:
					self["statusbar"].setText(_("Library lmxl is not installed!\nTry to install the library again or change the method of processing data in the settings menu."))
				return
			if len(results) == 0:
				self["statusbar"].setText(_("Nothing found for: %s or no answer in kinopoisk.ru") % (self.eventName))
				self["title"].setText("")
				eventname = self.eventName
				self.curResult = False
				return False
			self.resultlist = []
			for searchResult in results:
				try:
					self.resultlist.append(searchResult)
					total = len(results)
					if len(results) > 0:
						self["statusbar"].setText(_("Total results: %s") % (total))
					eventname = self.eventName
					self.curResult = True
				except:
					self.curResult = False
			self.showMenu()
			self["menu"].setList(self.resultlist)
		else:
			self["title"].setText(_("Enter or choose event for search ..."))

	def selectionChanged(self):
		self["titlelabel"].setText("")
		current = self["menu"].getCurrent()
		if current and self.curResult:
			try:
				genre = current[2]
			except:
				genre = ''
			if genre != '':
				self["titlelabel"].setText("%s" % (genre))

	def KinoRuPoster(self):
		if not self.curResult:
			self.removCovers()
		if fileExists("/tmp/preview.jpg"):
			jpg_file = "/tmp/preview.jpg"
		else:
			jpg_file = resolveFilename(SCOPE_PLUGINS, "Extensions/TMBD/picon_default.png")
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(jpg_file)

	def textNo(self, text):
		if text == None or text == "0":
			return ''
		else:
			return _("/ Duration: ") + text + _(" min.")

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None and self.curResult and self.curPoster:
			self["poster"].instance.setPixmap(ptr.__deref__())
			self["poster"].show()
		else:
			self["poster"].hide()

	def createSummary(self):
		#return KinoRuLCDScreen
		pass

#class KinoRuLCDScreen(Screen):
#	skin = """
#	<screen position="0,0" size="132,64" title="TMBD Details">
#		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
#		<widget source="parent.title" render="Label" position="6,26" size="120,34" font="Regular;14"/>
#
#	def __init__(self, session, parent):
#		Screen.__init__(self, session, parent)
#		self["headline"] = Label(_("Search in kinopoisk.ru"))


class MovielistPreviewScreen(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		self["background"] = Label("")
		self["preview"] = Pixmap()
		self.onShow.append(self.movePosition)

	def movePosition(self):
		if self.instance:
			self.instance.move(ePoint(config.plugins.tmbd.position_x.value, config.plugins.tmbd.position_y.value))
			size = config.plugins.tmbd.size.value.split("x")
			self.instance.resize(eSize(int(size[0]), int(size[1])))
			self["background"].instance.resize(eSize(int(size[0]), int(size[1])))
			self["preview"].instance.resize(eSize(int(size[0]), int(size[1])))

class MovielistPreview():
	def __init__(self):
		self.dialog = None
		self.mayShow = True
		self.working = False
		self.path = config.plugins.tmbd.cover_dir.value + 'covers/'
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.showPreviewCallback)

	def gotSession(self, session):
		if not self.dialog and session:
			self.dialog = session.instantiateDialog(MovielistPreviewScreen)

	def changeVisibility(self):
		if config.plugins.tmbd.enabled.value:
			config.plugins.tmbd.enabled.value = False
		else:
			config.plugins.tmbd.enabled.value = True
		config.plugins.tmbd.enabled.save()
		self.hideDialog()

	def showPreview(self, movie):
		if not self.dialog:
			self.gotSession(_session)
			if not self.dialog:
				return
		self.dialog.hide()
		if not self.working:
			if movie and self.mayShow and config.plugins.tmbd.enabled.value:
				png2 = os.path.split(movie)[1]
				if movie.endswith(".ts"):
					if fileExists("%s.meta"%(movie)):
						readmetafile = open("%s.meta"%(movie), "r")
						servicerefname = readmetafile.readline()[0:-1]
						eventname = readmetafile.readline()[0:-1]
						readmetafile.close()
						png2 = eventname
				png = self.path + png2 + ".jpg"
				if fileExists(png):
					self.working = True
					sc = AVSwitch().getFramebufferScale()
					size = config.plugins.tmbd.size.value.split("x")
					self.picload.setPara((int(size[0]), int(size[1]), sc[0], sc[1], False, 1, "#00000000"))
					self.picload.startDecode(png)

	def showPreviewCallback(self, picInfo=None):
		if not self.dialog:
			self.gotSession(_session)
			if not self.dialog:
				return
		self.dialog.hide()
		if picInfo:
			ptr = self.picload.getData()
			if ptr != None and self.working:
				self.dialog["preview"].instance.setPixmap(ptr)
				self.dialog.show()
		self.working = False

	def hideDialog(self):
		if not self.dialog:
			self.gotSession(_session)
			if not self.dialog:
				return
		self.mayShow = False
		self.dialog.hide()
		self.working = False

	def showDialog(self):
		if not self.dialog:
			self.gotSession(_session)
			if not self.dialog:
				return
		self.mayShow = True
		self.dialog.show()
		self.working = True

movielistpreview = MovielistPreview()

class MovielistPreviewPositionerCoordinateEdit(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,110" title="%s">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="0,45" size="560,60" scrollbarMode="showOnDemand" />
		</screen>""" % _("Poster Preview")

	def __init__(self, session, x, y, w, h):
		Screen.__init__(self, session)
		
		self["key_green"] = Label(_("OK"))
		
		self.xEntry = ConfigInteger(default=x, limits=(0, w))
		self.yEntry = ConfigInteger(default=y, limits=(0, h))
		ConfigListScreen.__init__(self, [
			getConfigListEntry("x position:", self.xEntry),
			getConfigListEntry("y position:", self.yEntry)])
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"green": self.ok,
				 "cancel": self.close
			}, -1)

	def ok(self):
		self.close([self.xEntry.value, self.yEntry.value])

class MovielistPreviewPositioner(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		self["background"] = Label("")
		self["preview"] = Pixmap()
		
		self["actions"] = ActionMap(["EPGSelectActions", "MenuActions", "WizardActions"],
		{
			"left": self.left,
			"up": self.up,
			"right": self.right,
			"down": self.down,
			"ok": self.ok,
			"back": self.exit,
			"menu": self.editCoordinates,
			"nextBouquet": self.bigger,
			"prevBouquet": self.smaller
		}, -1)
		
		desktop = getDesktop(0)
		self.desktopWidth = desktop.size().width()
		self.desktopHeight = desktop.size().height()
		
		self.moveTimer = eTimer()
		self.moveTimer.callback.append(self.movePosition)
		self.moveTimer.start(50, 1)
		
		self.onShow.append(self.__onShow)

	def __onShow(self):
		if self.instance:
			size = config.plugins.tmbd.size.value.split("x")
			self.instance.resize(eSize(int(size[0]), int(size[1])))
			self["background"].instance.resize(eSize(int(size[0]), int(size[1])))
			self["preview"].instance.resize(eSize(int(size[0]), int(size[1])))

	def movePosition(self):
		self.instance.move(ePoint(config.plugins.tmbd.position_x.value, config.plugins.tmbd.position_y.value))
		self.moveTimer.start(50, 1)

	def left(self):
		value = config.plugins.tmbd.position_x.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.tmbd.position_x.value = value

	def up(self):
		value = config.plugins.tmbd.position_y.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.tmbd.position_y.value = value

	def right(self):
		value = config.plugins.tmbd.position_x.value
		value += 1
		if value > self.desktopWidth:
			value = self.desktopWidth
		config.plugins.tmbd.position_x.value = value

	def down(self):
		value = config.plugins.tmbd.position_y.value
		value += 1
		if value > self.desktopHeight:
			value = self.desktopHeight
		config.plugins.tmbd.position_y.value = value

	def ok(self):
		config.plugins.tmbd.position_x.save()
		config.plugins.tmbd.position_y.save()
		self.close()

	def exit(self):
		config.plugins.tmbd.position_x.cancel()
		config.plugins.tmbd.position_y.cancel()
		self.close()

	def editCoordinates(self):
		self.session.openWithCallback(self.editCoordinatesCallback, MovielistPreviewPositionerCoordinateEdit, config.plugins.tmbd.position_x.value, config.plugins.tmbd.position_y.value, self.desktopWidth, self.desktopHeight)

	def editCoordinatesCallback(self, callback=None):
		if callback:
			config.plugins.tmbd.position_x.value = callback[0]
			config.plugins.tmbd.position_y.value = callback[1]

	def bigger(self):
		if config.plugins.tmbd.size.value == "185x278":
			config.plugins.tmbd.size.value = "285x398"
		elif config.plugins.tmbd.size.value == "130x200":
			config.plugins.tmbd.size.value = "185x278"
		elif config.plugins.tmbd.size.value == "104x150":
			config.plugins.tmbd.size.value = "130x200"
		config.plugins.tmbd.size.save()
		self.__onShow()

	def smaller(self):
		if config.plugins.tmbd.size.value == "130x200":
			config.plugins.tmbd.size.value = "104x150"
		elif config.plugins.tmbd.size.value == "185x278":
			config.plugins.tmbd.size.value = "130x200"
		elif config.plugins.tmbd.size.value == "285x398":
			config.plugins.tmbd.size.value = "185x278"
		config.plugins.tmbd.size.save()
		self.__onShow()

class MovielistPreviewMenu(Screen):
	skin = """
		<screen position="center,center" size="420,105" title="%s">
			<widget name="list" position="5,5" size="410,100" />
		</screen>""" % _("Poster Preview")

	def __init__(self, session, service):
		Screen.__init__(self, session)
		self.session = session
		self.service = service
		self["list"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self.showMenu)

	def showMenu(self):
		list = []
		if config.plugins.tmbd.enabled.value:
			list.append(_("Deactivate Poster Preview"))
		else:
			list.append(_("Activate Poster Preview"))
		list.append(_("Change Poster Preview position"))
		self["list"].setList(list)

	def okClicked(self):
		idx = self["list"].getSelectionIndex()
		if movielistpreview.dialog is None:
			movielistpreview.gotSession(self.session)
		if idx == 0:
			movielistpreview.changeVisibility()
			self.showMenu()
		else:
			movielistpreview.dialog.hide()
			self.session.open(MovielistPreviewPositioner)

SelectionChanged = MovieList.selectionChanged

def selectionChanged(instance):
	global movie2
	movie2 = ''
	SelectionChanged(instance)
	curr = instance.getCurrent()
	if curr and isinstance(curr, eServiceReference):
		movielistpreview.showPreview(curr.getPath())
		movie2 = curr.getPath()
	else:
		movielistpreview.hideDialog()
MovieList.selectionChanged = selectionChanged

Hide = MovieSelection.hide
def hideMovieSelection(instance):
	Hide(instance)
	movielistpreview.hideDialog()
MovieSelection.hide = hideMovieSelection

Show = MovieSelection.show
def showMovieSelection(instance):
	Show(instance)
	movielistpreview.showDialog()
MovieSelection.show = showMovieSelection

class EventChoiseList:
	def __init__(self, session):
		self.session = session
		global eventname, eventname_now, eventname_next
		cur_name = ""
		eventname = ""
		eventname_now = ""
		eventname_next = ""
		profile = ""
		cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if cur_ref:
			refstr = cur_ref.toString()
			cur_name = ServiceReference(eServiceReference(refstr)).getServiceName()
		s = self.session.nav.getCurrentService()
		info = s and s.info()
		event_now = info and info.getEvent(0)	# 0 = now
		if event_now:
			eventName = event_now.getEventName().split("(")[0].strip()
			eventname_now = cutName(eventName)
		event_next = info and info.getEvent(1)	# 1 = next
		if event_next:
			eventName = event_next.getEventName().split("(")[0].strip()
			eventname_next = cutName(eventName)
		if event_now and event_next:
			keyslist = [ ]
			eventlist = [
			(_("Now: %s") % (eventname_now), self.Nowevent),
			(_("Next: %s") % (eventname_next), self.Nextevent),
			]
			if config.plugins.tmbd.profile.value == "0":
				profile = "themoviedb.org"
			else:
				profile = "kinopoisk.ru"
			keyslist.extend( [ "1", "2" ] )
			eventlist.append((_('Change profile'), self.ChangeProfile))
			keyslist.append('blue')
			dlg = self.session.openWithCallback(self.menuCallback,ChoiceBox,list = eventlist,keys = keyslist,title= _("%s\nProfile: %s\nSelect event for search:") % (cur_name, profile))
			dlg.setTitle(_("TMBD Details"))
		elif event_now and not event_next:
			self.Nowevent()
		else:
			if config.plugins.tmbd.no_event.value:
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname, False)
				else:
					self.session.open(KinoRu, eventname, False)

	def ChangeProfile(self):
		if config.plugins.tmbd.profile.value == "0":
			config.plugins.tmbd.profile.value = "1"
		else:
			config.plugins.tmbd.profile.value = "0"
		config.plugins.tmbd.profile.save()

		
	def Nowevent(self):
		global eventname, eventname_now, eventname_next
		eventname = eventname_now
		if config.plugins.tmbd.profile.value == "0":
			self.session.open(TMBD, eventname, False)
		else:
			self.session.open(KinoRu, eventname, False)
	
	def Nextevent(self):
		global eventname, eventname_now, eventname_next
		eventname = eventname_next
		if config.plugins.tmbd.profile.value == "0":
			self.session.open(TMBD, eventname, False)
		else:
			self.session.open(KinoRu, eventname, False)
			
	def menuCallback(self, ret = None):
		ret and ret[1]()
		
class MovielistProfileList(Screen):
	skin = """
		<screen position="center,center" size="380,80" title="%s">
			<widget name="list" position="5,5" size="370,75" />
		</screen>""" % _("Select Profile")

	def __init__(self, session, eventname):
		Screen.__init__(self, session)
		self.session = session
		self.eventname = eventname
		self["list"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self.showMenu)

	def showMenu(self):
		list = []
		if config.plugins.tmbd.movielist_profile.value == "2":
			list.append(_("kinopoisk.ru"))
			list.append(_("themoviedb.org"))
		if config.plugins.tmbd.movielist_profile.value == "1":
			list.append(_("themoviedb.org"))
			list.append(_("kinopoisk.ru"))
		self["list"].setList(list)

	def okClicked(self):
		sel = self["list"].getCurrent()
		if sel == _("kinopoisk.ru"):
			self.session.open(KinoRu, self.eventname, movielist = True)
		if sel == _("themoviedb.org"):
			self.session.open(TMBD, self.eventname, movielist = True)

def eventinfo(session, eventName="", **kwargs):
	if eventName != "":
		eventName = cutName(eventName)
		if config.plugins.tmbd.profile.value == "0":
			session.open(TMBD, eventName)
		else:
			session.open(KinoRu, eventName)
	else:
		ref = session.nav.getCurrentlyPlayingServiceReference()
		session.open(TMBDEPGSelection, ref)

#def showExtendedServiceInfo(session, service, **kwargs):
#	from enigma import eServiceReference
#	if service and (service.flags & eServiceReference.isDirectory):
#		servtype = "directory"
#	else:
#		servtype = "service"
#	print "Тип сервиса:",  servtype
	
#	infotype = kwargs.get("info", "")
#	if infotype == "poster":
#		print "Надо показать постер(ы)!"
#	elif infotype == "details":
#		print "Надо показать детали!"
#	else:
#		print "Эта функция вызвана не из меню списка записей!!!"


#myMovieSelection.defMovieContextMenu = myMovieSelection.MovieContextMenu
#class newMovieContextMenu(myMovieSelection.defMovieContextMenu):
#	try:
#		def __init__(self, session, csel, service):
#			myMovieSelection.defMovieContextMenu.__init__(self, session, csel, service)
#			self.skinName = "MovieContextMenu"
#			idx = 2
#			if service:
#				if (service.flags & eServiceReference.mustDescent):
#					#self["menu"].list.insert(idx, (_("Search movie in TMBD"),boundFunction(movielist, session, service)))
#					for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST):
#						if _("Search movie in TMBD") in str(p.name):
#							append_to_menu( menu, (p.description, boundFunction(p, session, service)), key="bullet")
#							break
#					#self["menu"].list.insert(idx, (_("Show Poster"),boundFunction(showExtendedServiceInfo, session, service,info="poster")))
#					#self["menu"].list.insert(idx, (_("Show Details"),boundFunction(showExtendedServiceInfo, session, service,info="details")))
#	except:
#		pass
#myMovieSelection.MovieContextMenu = newMovieContextMenu


def main(session, **kwargs):
	session.open(TMBDSettings)

def main3(session, eventName="", **kwargs):
	global eventname
	eventname = ""
	s = session.nav.getCurrentService()
	info = s and s.info()
	event = info and info.getEvent(0)	# 0 = now
	if config.plugins.tmbd.ext_menu_event.value == "0":
		if event:
			eventName = event.getEventName().split("(")[0].strip()
			eventname = cutName(eventName)
			if config.plugins.tmbd.profile.value == "0":
				session.open(TMBD, eventname)
			else:
				session.open(KinoRu, eventname)
		else:
			if config.plugins.tmbd.no_event.value:
				if config.plugins.tmbd.profile.value == "0":
					session.open(TMBD, eventname)
				else:
					session.open(KinoRu, eventname)
	else:
		EventChoiseList(session)

from keyids import KEYIDS
from enigma import eActionMap

class TMBDInfoBar:
	def __init__(self, session, infobar):
		self.session = session
		self.infobar = infobar
		self.lastKey = None
		self.hotkeys = { }
		for x in TMBDInfoBarKeys:
			self.hotkeys[x[0]] = [KEYIDS[key] for key in x[2]]
		eActionMap.getInstance().bindAction('', -10, self.keyPressed)

	def keyPressed(self, key, flag):
		for k in self.hotkeys[config.plugins.tmbd.hotkey.value]:
			if key == k and self.session.current_dialog == self.infobar:
				if flag == 0:
					self.lastKey = key
				elif self.lastKey != key or flag == 4:
					self.lastKey = None
					continue
				elif flag == 3:
					self.lastKey = None
					self.execute()
				elif flag == 1:
					self.lastKey = None
					self.showChoiceEvent()
				return 1
		return 0
		
	def execute(self):
		self.session.open(TMBDSettings)

	def showChoiceEvent(self):
		global eventname
		eventname = ""
		s = self.session.nav.getCurrentService()
		info = s and s.info()
		event = info and info.getEvent(0)	# 0 = now
		if config.plugins.tmbd.ext_menu_event.value == "0":
			if event:
				eventName = event.getEventName().split("(")[0].strip()
				eventname = cutName(eventName)
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname)
				else:
					self.session.open(KinoRu, eventname)
			else:
				if config.plugins.tmbd.no_event.value:
					if config.plugins.tmbd.profile.value == "0":
						self.session.open(TMBD, eventname)
					else:
						self.session.open(KinoRu, eventname)
		else:
			self.EventChoiselist()

	def EventChoiselist(self):
		global eventname, eventname_now, eventname_next
		cur_name = ""
		eventname = ""
		eventname_now = ""
		eventname_next = ""
		profile = ""
		cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if cur_ref:
			refstr = cur_ref.toString()
			cur_name = ServiceReference(eServiceReference(refstr)).getServiceName()
		s = self.session.nav.getCurrentService()
		info = s and s.info()
		event_now = info and info.getEvent(0)	# 0 = now
		if event_now:
			eventName = event_now.getEventName().split("(")[0].strip()
			eventname_now = cutName(eventName)

		event_next = info and info.getEvent(1)	# 1 = next
		if event_next:
			eventName = event_next.getEventName().split("(")[0].strip()
			eventname_next = cutName(eventName)
		if event_now and event_next:
			keyslist = [ ]
			eventlist = [
			(_("Now: %s") % (eventname_now), self.Nowevent),
			(_("Next: %s") % (eventname_next), self.Nextevent),
			]
			if config.plugins.tmbd.profile.value == "0":
				profile = "themoviedb.org"
			else:
				profile = "kinopoisk.ru"
			keyslist.extend( [ "1", "2" ] )
			eventlist.append((_('Change profile'), self.ChangeProfile))
			keyslist.append('blue')
			dlg = self.session.openWithCallback(self.menuCallback,ChoiceBox,list = eventlist,keys = keyslist,title= _("%s\nProfile: %s\nSelect event for search:") % (cur_name, profile))
			dlg.setTitle(_("TMBD Details"))
		elif event_now and not event_next:
			self.Nowevent()
		else:
			if config.plugins.tmbd.no_event.value:
				if config.plugins.tmbd.profile.value == "0":
					self.session.open(TMBD, eventname, False)
				else:
					self.session.open(KinoRu, eventname, False)

	def ChangeProfile(self):
		if config.plugins.tmbd.profile.value == "0":
			config.plugins.tmbd.profile.value = "1"
		else:
			config.plugins.tmbd.profile.value = "0"
		config.plugins.tmbd.profile.save()

	def Nowevent(self):
		global eventname, eventname_now, eventname_next
		eventname = eventname_now
		if config.plugins.tmbd.profile.value == "0":
			self.session.open(TMBD, eventname, False)
		else:
			self.session.open(KinoRu, eventname, False)
	
	def Nextevent(self):
		global eventname, eventname_now, eventname_next
		eventname = eventname_next
		if config.plugins.tmbd.profile.value == "0":
			self.session.open(TMBD, eventname, False)
		else:
			self.session.open(KinoRu, eventname, False)
			
	def menuCallback(self, ret = None):
		ret and ret[1]()

def movielist(session, service, **kwargs):
	global name
	global eventname
	eventName=""
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	name = info and info.getName(service) or ''
	eventName = name.split(".")[0].strip()
	eventname = eventName
	if config.plugins.tmbd.movielist_profile.value == "0":
		if config.plugins.tmbd.profile.value == "0":
			session.open(TMBD, eventname, movielist = True)
		else:
			session.open(KinoRu, eventname, movielist = True)
	else:
		session.open(MovielistProfileList, eventname)

def autostart_ChannelContextMenu(session, **kwargs):
	TMBDChannelContextMenuInit()

baseInfoBar__init__ = None
def tmbdInfoBar__init__(self, session):
	baseInfoBar__init__(self, session)
	self.tmbdinfobar = TMBDInfoBar(session, self)

def sessionstart(reason, **kwargs):
	if reason == 0:
		global _session, def_SelectionEventInfo_updateEventInfo
		if _session is None:
			_session = kwargs["session"]
		movielistpreview.gotSession(kwargs["session"])
		if def_SelectionEventInfo_updateEventInfo is None:
			def_SelectionEventInfo_updateEventInfo = SelectionEventInfo.updateEventInfo
			SelectionEventInfo.updateEventInfo = new_SelectionEventInfo_updateEventInfo
		global def_MovieSelection_showEventInformation
		if def_MovieSelection_showEventInformation is None:
			def_MovieSelection_showEventInformation = MovieSelection.showEventInformation
			MovieSelection.showEventInformation = new_MovieSelection_showEventInformation

def autostart(reason, **kwargs):
	if reason == 0:
		global baseInfoBar__init__
		from Screens.InfoBar import InfoBar
		if baseInfoBar__init__ is None:
			baseInfoBar__init__ = InfoBar.__init__
		InfoBar.__init__ = tmbdInfoBar__init__
		#try:
		#	EPGSelectionInit()
		#except Exception:
		#	pass
		#if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG/plugin.pyc"):
		#	try:
		#		GraphMultiEPGInit()
		#	except Exception:
		#		pass
		#if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/nStreamVOD/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/nStreamVOD/plugin.pyc"):
		#	try:
		#		nStreamVODInit()
		#	except Exception:
		#		pass

def main2(session, service):
	session.open(MovielistPreviewMenu, service)

def epgfurther(session, selectedevent, **kwargs):
	try:
		eventName = selectedevent[0].getEventName()
	except:
		eventName = ""
	if eventName != "":
		eventName = cutName(eventName)
		if config.plugins.tmbd.profile.value == "0":
			session.open(TMBD, eventName)
		else:
			session.open(KinoRu, eventName)

def yteventinfo(session, eventName="", **kwargs):
	if session is None: return
	if eventName != "":
		eventName = cutName(eventName)
		if config.plugins.tmbd.yt_start.value == "0":
			session.open(tmbdYTTrailer.TmbdYTTrailerList, eventName)
		else:
			ytTrailer = tmbdYTTrailer.tmbdYTTrailer(session)
			ytTrailer.showTrailer(eventName)
	else:
		s = session.nav.getCurrentService()
		info = s and s.info()
		event_now = info and info.getEvent(0)
		if event_now:
			event = event_now.getEventName() or ''
			eventName = event.split("(")[0].strip()
			eventName = cutName(eventName)
			if config.plugins.tmbd.yt_start.value == "0":
				session.open(tmbdYTTrailer.TmbdYTTrailerList, eventName)
			else:
				ytTrailer = tmbdYTTrailer.tmbdYTTrailer(session)
				ytTrailer.showTrailer(eventName)

def ytfurther(session, selectedevent, **kwargs):
	try:
		eventName = selectedevent[0].getEventName()
	except:
		eventName = ""
	if eventName != "":
		eventName = cutName(eventName)
		if config.plugins.tmbd.yt_start.value == "0":
			session.open(tmbdYTTrailer.TmbdYTTrailerList, eventName)
		else:
			ytTrailer = tmbdYTTrailer.tmbdYTTrailer(session)
			ytTrailer.showTrailer(eventName)

def Plugins(**kwargs):
	if config.plugins.tmbd.add_ext_menu.value:
		path = [PluginDescriptor(name=_("TMBD Details"),
				description=_("Setup menu"),
				icon="tmdb.png",
				where=PluginDescriptor.WHERE_PLUGINMENU,
				fnc=main,
				),
				PluginDescriptor(name=_("TMBD details for event"),
				description=_("Query details from the Internet Movie Database"),
				where=PluginDescriptor.WHERE_EVENTINFO,
				fnc=eventinfo,
				),
				PluginDescriptor(name=_("Search movie in TMBD"),
				description = _("Search movie in TMBD"),
				where = PluginDescriptor.WHERE_MOVIELIST,
				fnc = movielist,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_SESSIONSTART,
				fnc = autostart_ChannelContextMenu,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_SESSIONSTART,
				fnc = sessionstart,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_AUTOSTART,
				fnc = autostart,
				),
				PluginDescriptor(name=_("Poster Preview (TMBD)"),
				description=_("Poster Preview (TMBD)"),
				where=PluginDescriptor.WHERE_MOVIELIST,
				fnc=main2,
				),
				PluginDescriptor(name=_("TMBD Details:current event"),
				description=_("Query details from the Internet Movie Database"),
				where=PluginDescriptor.WHERE_EXTENSIONSMENU,
				fnc=main3,
				),
		]
	else:
		path = [PluginDescriptor(name=_("TMBD Details"),
				description=_("Setup menu"),
				icon="tmdb.png",
				where=PluginDescriptor.WHERE_PLUGINMENU,
				fnc=main,
				),
				PluginDescriptor(name=_("TMBD details for event"),
				description=_("Query details from the Internet Movie Database"),
				where=PluginDescriptor.WHERE_EVENTINFO,
				fnc=eventinfo,
				),
				PluginDescriptor(name=_("Search movie in TMBD"),
				description = _("Search for movie in TMBD"),
				where = PluginDescriptor.WHERE_MOVIELIST,
				fnc = movielist,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_SESSIONSTART,
				fnc = autostart_ChannelContextMenu,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_SESSIONSTART,
				fnc = sessionstart,
				),
				PluginDescriptor(
				where = PluginDescriptor.WHERE_AUTOSTART,
				fnc = autostart,
				),
				PluginDescriptor(name=_("Poster Preview (TMBD)"),
				description=_("Poster Preview (TMBD)"),
				where=PluginDescriptor.WHERE_MOVIELIST,
				fnc=main2,
				),
			]
	if epg_furtherOptions and config.plugins.tmbd.show_in_furtheroptionsmenu.value:
		path.append(PluginDescriptor(name = _("Search event in TMBD"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = epgfurther))
	yt_event_menu = config.plugins.tmbd.yt_event_menu.value
	if yt_event_menu != "0":
		if yt_event_menu == "1":
			path.append(PluginDescriptor(name = _("Search yt-trailer for event"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = ytfurther))
		elif yt_event_menu == "2":
			path.append(PluginDescriptor(name = _("Search yt-trailer for event"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = yteventinfo))
		else:
			if epg_furtherOptions:
				path.append(PluginDescriptor(name = _("Search yt-trailer for event"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = ytfurther))
			path.append(PluginDescriptor(name = _("Search yt-trailer for event"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = yteventinfo))
	return path
