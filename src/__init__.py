# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
from sys import version_info
import gettext
def localeInit():
	lang = language.getLanguage()[:2]
	os_environ["LANGUAGE"] = lang
	gettext.bindtextdomain("TMBD", resolveFilename(SCOPE_PLUGINS, "Extensions/TMBD/locale"))

def _(txt):
	t = gettext.dgettext("TMBD", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

# Disable certificate verification on python 2.7.9
sslContext = None
if version_info >= (2, 7, 9):
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except:
		pass
