import os

from json import load
from urllib import quote
from urllib2 import urlopen
from twisted.web.client import downloadPage

from enigma import ePicLoad, eTimer, eServiceReference
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigInteger, ConfigSelection, \
	ConfigSubsection, ConfigText, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from . import _


config.plugins.tmbd_yttrailer = ConfigSubsection()
config.plugins.tmbd_yttrailer.best_resolution = ConfigSelection(default='22', choices=[
	('38', '4096x3072'), ('37', '1920x1080'), ('22', '1280x720'), ('35', '854x480'),
	('18', '640x360'), ('5', '400x240'), ('17', '176x144')])
config.plugins.tmbd_yttrailer.ext_descr = ConfigText(default = '', fixed_size = False)
config.plugins.tmbd_yttrailer.max_results = ConfigInteger(5, limits = (1, 10))
config.plugins.tmbd_yttrailer.close_player_with_exit = ConfigYesNo(False)
config.plugins.tmbd_yttrailer.search = ConfigSelection(choices = [("1", _("Press OK"))], default = "1")


from YouTubeVideoUrl import YouTubeVideoUrl

API_KEY = 'AIzaSyDo0EKjcqXPqoMwmWHMwFAdpwF9K8_p6T0'


class tmbdYTTrailer:
	def __init__(self, session):
		self.session = session
		self.ytdl = YouTubeVideoUrl()

	def showTrailer(self, eventname):
		if eventname:
			feeds = self.getYTFeeds(eventname, 1)
			if not feeds:
				self.showError()
			else:
				ref = self.setServiceReference(feeds[0])
				if ref:
					self.session.open(tmbdTrailerPlayer, ref)
				else:
					self.showError()

	def getYTFeeds(self, eventname, max_results):
		if config.plugins.tmbd_yttrailer.best_resolution.value not in ['35', '18', '5', '17']:
			eventname += ' HD'
		eventname += ' Trailer'
		if config.plugins.tmbd_yttrailer.ext_descr.value:
			eventname += ' ' + config.plugins.tmbd_yttrailer.ext_descr.value
		try:
			feeds = self.get_response(eventname, max_results)
		except:
			return None
		if len(feeds) > 0:
			return feeds
		return None

	def get_response(self, query, max_results):
		videos = []
		url = 'https://www.googleapis.com/youtube/v3/search?part=id%2Csnippet&maxResults=' + \
			str(max_results) + '&q=' + quote(query) + '&type=video&key=' + API_KEY
		response = urlopen(url)
		response = load(response)
		for result in response.get('items', []):
			videos.append((result['id']['videoId'], 
				str(result['snippet']['title']),
				str(result['snippet']['thumbnails']['default']['url']),
				None))
		return videos

	def setServiceReference(self, entry):
		try:
			url = self.ytdl.extract(entry[0])
		except:
			return None
		if url:
			ref = eServiceReference(4097, 0, url)
			ref.setName(entry[1])
			return ref
		return None

	def showError(self):
		from Screens.MessageBox import MessageBox
		self.session.open(MessageBox, _('Problems with YT-Feeds!'), MessageBox.TYPE_INFO)


class TmbdYTTrailerList(Screen, tmbdYTTrailer):
	skin = """
		<screen name="TmbdYTTrailerList" position="center,center" size="630,380" title="YT Trailer-List">
			<widget source="list" render="Listbox" position="center,center" size="610,360" \
				scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent" >
					{"template": [
						MultiContentEntryPixmapAlphaTest(pos=(0,0), \
							size=(100,72), png=3), # Thumbnail
						MultiContentEntryText(pos=(110,1), size=(500,70), \
							font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=1)],
					"fonts": [gFont("Regular",20)],
					"itemHeight": 72}
				</convert>
			</widget>
			<widget name="thumbnail" position="0,0" size="100,72" /> # Thumbnail size in list
		</screen>"""
	def __init__(self, session, eventname):
		Screen.__init__(self, session)
		tmbdYTTrailer.__init__(self, session)
		self.session = session
		self.eventName = eventname
		self['actions'] = ActionMap(['WizardActions', 'MenuActions'],
		{
			'ok': self.okPressed,
			'menu': self.menuPressed,
			'back': self.close
		}, -2)
		self['list'] = List([])
		self['thumbnail'] = Pixmap()
		self['thumbnail'].hide()
		self.picloads = {}
		self.thumbnails = {}
		self.sc = AVSwitch().getFramebufferScale()
		self.thumbnailTaimer = eTimer()
		self.thumbnailTaimer.timeout.callback.append(self.updateThumbnails)
		self.onLayoutFinish.append(self.startRun)

	def startRun(self, manual=False):
		self.setTitle(_('YT Trailer-List'))
		if not self.eventName:
			self.close()
		self.feeds = self.getYTFeeds(self.eventName, config.plugins.tmbd_yttrailer.max_results.value)
		if self.feeds:
			self['list'].setList(self.feeds)
			self.createThumbnails()
		elif not manual:
			# I hope that happens rarely, so set up timer only here
			self.errorTaimer = eTimer()
			self.errorTaimer.timeout.callback.append(self.errorTaimerStop)
			self.errorTaimer.start(1)

	def menuPressed(self):
		self.session.openWithCallback(self.setSearchString, VirtualKeyBoard, title = _("Enter text for search YT-Trailer:"))

	def setSearchString(self, ret=None):
		if ret and ret != '':
			self.eventName = ret
			self.picloads = {}
			self.thumbnails = {}
			self['list'].setList([])
			self.startRun(True)

	def createThumbnails(self):
		for entry in self.feeds:
			if not entry[2]:
				self.decodeThumbnail(entry[0])
			else:
				downloadPage(entry[2], os.path.join('/tmp/', str(entry[0]) + '.jpg'))\
					.addCallback(boundFunction(self.downloadFinished, entry[0]))\
					.addErrback(boundFunction(self.downloadFailed, entry[0]))

	def downloadFinished(self, entryId, result):
		image = os.path.join('/tmp/', str(entryId) + '.jpg')
		self.decodeThumbnail(entryId, image)

	def downloadFailed(self, entryId, result):
		print "[TMBD] Thumbnail download failed!"
		self.decodeThumbnail(entryId)

	def decodeThumbnail(self, entryId, image = None):
		if not image or not os.path.exists(image):
			print "[TMBD] Thumbnail not exists, use default for", entryId
			image = resolveFilename(SCOPE_PLUGINS,
				'Extensions/TMBD/yt_default.png')
		self.picloads[entryId] = ePicLoad()
		self.picloads[entryId].PictureData.get()\
			.append(boundFunction(self.FinishDecode, entryId, image))
		self.picloads[entryId].setPara((
			self['thumbnail'].instance.size().width(),
			self['thumbnail'].instance.size().height(),
			self.sc[0], self.sc[1], False, 1, '#00000000'))
		self.picloads[entryId].startDecode(image)

	def FinishDecode(self, entryId, image, picInfo = None):
		ptr = self.picloads[entryId].getData()
		if ptr:
			self.thumbnails[entryId] = ptr
			del self.picloads[entryId]
			if image[:4] == '/tmp':
				os.remove(image)
			self.thumbnailTaimer.start(1)

	def updateThumbnails(self):
		self.thumbnailTaimer.stop()
		if len(self.picloads) != 0:
			self.thumbnailTaimer.start(1)
		else:
			count = 0
			for entry in self.feeds:
				if entry[0] in self.thumbnails:
					self.feeds[count] = (entry[0], entry[1], entry[2],
						self.thumbnails[entry[0]])
					del self.thumbnails[entry[0]]
				count += 1
			self['list'].updateList(self.feeds)

	def okPressed(self):
		entry = self['list'].getCurrent()
		if not entry:
			self.showError()
		else:
			ref = self.setServiceReference(entry)
			if ref:
				self.session.open(tmbdTrailerPlayer, ref)
			else:
				self.showError()

	def errorTaimerStop(self):
		self.errorTaimer.stop()
		del self.errorTaimer
		self.showError()
		self.close()

	def showError(self):
		from Screens.MessageBox import MessageBox
		self.session.open(MessageBox, _('Problems with YT-Feeds!'), MessageBox.TYPE_INFO)


class tmbdTrailerPlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = 'MoviePlayer'
		self.servicelist = InfoBar.instance and InfoBar.instance.servicelist
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave YT-Trailer player..."))
			})
		self["vcsActions"] = HelpableActionMap(self, "ColorActions",
			{
				"blue": (self.showVCS, _("show VCS..."))
			})
		if config.plugins.tmbd_yttrailer.close_player_with_exit.value:
			self["closeactions"] = HelpableActionMap(self, "WizardActions",
				{
					"back": (self.close, _("leave YT-Trailer player..."))
				})
		self.setTitle(_("YT-Trailer Player"))

	def leavePlayer(self):
		self.close()

	def doEofInternal(self, playing):
		self.close()

	def showMovies(self):
		pass

	def openServiceList(self):
		if hasattr(self, 'toggleShow'):
			self.toggleShow()

	def showVCS(self):
		try:
			from Plugins.Extensions.VCS.plugin import show_choisebox
		except:
			pass
		else:
			try:
				show_choisebox(self.session)
			except:
				pass

class TmbdYTTrailerSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ['tmbdYTTrailerSetup', 'Setup']
		self.setTitle(_("YT-Trailer Setup"))
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Save'))
		self['description'] = Label('')
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'],
			{
				'cancel': self.keyCancel,
				'red': self.keyCancel,
				'ok': self.keySearch,
				'green': self.keySave
			}, -2)
		configlist = []
		ConfigListScreen.__init__(self, configlist, session = session)
		configlist.append(getConfigListEntry(_('Extended search filter'), 
			config.plugins.tmbd_yttrailer.ext_descr,
			_('Set extended search filter, e.g. ru.')))
		configlist.append(getConfigListEntry(_('Best resolution for first found'),
			config.plugins.tmbd_yttrailer.best_resolution,
			_('What maximum resolution used, if available.\nIf you have a slow Internet connection, you can use a lower resolution.')))
		configlist.append(getConfigListEntry(_('Results in list mode'), 
			config.plugins.tmbd_yttrailer.max_results,
			_('How many search results will be returned in list mode.')))
		configlist.append(getConfigListEntry(_("Close Player with exit-key"),
			config.plugins.tmbd_yttrailer.close_player_with_exit,
			_('When not enabled, Player close with only stop key.')))
		configlist.append(getConfigListEntry(_("Manual search"),
			config.plugins.tmbd_yttrailer.search,
			_('Press OK for manual search YT-Trailer.')))
		self['config'].list = configlist
		self['config'].l.setList(configlist)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_('YT-Trailer Setup'))

	def keySearch(self):
		self.session.openWithCallback(self.setSearchString, VirtualKeyBoard, title = _("Enter text for search YT-Trailer:"))

	def setSearchString(self, ret = None):
		if ret and ret != '':
			self.session.open(TmbdYTTrailerList, ret)