# -*- coding: utf-8 -*-
from os import environ as os_environ
#from urlparse import parse_qs
import re
from urllib2 import Request, URLError, HTTPError, urlopen as urlopen2, quote as urllib2_quote, unquote as urllib2_unquote
#import htmlentitydefs
import urllib
#import gettext
from socket import gaierror, error
import httplib, urllib, re
import urllib2
import string
import time
import os, socket
import sys
import traceback
import codecs
#from optparse import OptionParser
from BeautifulSoup import BeautifulSoup
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
std_headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
 'Accept-Charset': 'windows-1251,utf-8;q=0.7,*;q=0.7',
 'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
 'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3'}

def comment_out(str):
    s = str
    try:
        s = unicode(str, 'utf8')
    except:
        pass

    print '# %s' % (s,)


def debug_out(str):
    if VERBOSE:
        comment_out(str)


def response_out(str):
    if DUMP_RESPONSE:
        s = str
        try:
            s = unicode(str, 'utf8')
        except:
            pass

        print s


def print_exception(str):
    for line in str.splitlines():
        comment_out(line)


def normilize_string(processingstring):
    try:
        symbols_to_remove = {'&#160;': ' ',
         '&nbsp;': ' ',
         '&#161;': '\xc2\xa1',
         '&iexcl;': '\xc2\xa1',
         '&#162;': '\xc2\xa2',
         '&cent;': '\xc2\xa2',
         '&#163;': '\xc2\xa3',
         '&pound;': '\xc2\xa3',
         '&#164;': '\xc2\xa4',
         '&curren;': '\xc2\xa4',
         '&#165;': '\xc2\xa5',
         '&yen;': '\xc2\xa5',
         '&#166;': '\xc2\xa6',
         '&brvbar;': '\xc2\xa6',
         '&brkbar;': ',',
         '&#167;': '\xc2\xa7',
         '&sect;': '\xc2\xa7',
         '&#168;': '\xc2\xa8',
         '&uml;': '\xc2\xa8',
         '&#169;': '\xc2\xa9',
         '&copy;': '\xc2\xa9',
         '&#170;': '\xc2\xaa',
         '&ordf;': '\xc2\xaa',
         '&#171;': '\xc2\xab',
         '&laquo;': '\xc2\xab',
         '&#172;': '\xc2\xac',
         '&not;': '\xc2\xac',
         '&#173;': ' ',
         '&shy;': '\xc2\xad ',
         '&#174;': '\xc2\xae',
         '&reg;': '\xc2\xae',
         '&#175;': '\xc2\xaf',
         '&macr;': '\xc2\xaf',
         '&#176;': '\xc2\xb0',
         '&deg;': '\xc2\xb0',
         '&#177;': '\xc2\xb1',
         '&plusmn;': '\xc2\xb1',
         '&#178;': '\xc2\xb2',
         '&sup2;': '\xc2\xb2',
         '&#179;': '\xc2\xb3',
         '&sup3;': '\xc2\xb3',
         '&#180;': '\xc2\xb4',
         '&acute;': '\xc2\xb4',
         '&#181;': '\xc2\xb5',
         '&micro;': '\xc2\xb5',
         '&#182;': '\xc2\xb6',
         '&para;': '\xc2\xb6',
         '&#183;': '\xc2\xb7',
         '&middot;': '\xc2\xb7',
         '&#184;': '\xc2\xb8',
         '&cedil;': '\xc2\xb8',
         '&#185;': '\xc2\xb9',
         '&sup1;': '\xc2\xb9',
         '&#186;': '\xc2\xba',
         '&ordm;': '\xc2\xba',
         '&#187;': '\xc2\xbb',
         '&raquo;': '\xc2\xbb',
         '&#188;': '\xc2\xbc',
         '&frac14;': '\xc2\xbc',
         '&#189;': '\xc2\xbd',
         '&frac12;': '\xc2\xbd',
         '&#190;': '\xc2\xbe',
         '&frac34;': '\xc2\xbe',
         '&#191;': '\xc2\xbf',
         '&iquest;': '\xc2\xbf',
         '&#192;': '\xc3\x80',
         '&Agrave;': '\xc3\x80',
         '&#193;': '\xc3\x81',
         '&Aacute;': '\xc3\x81',
         '&#194;': '\xc3\x82',
         '&Acirc;': '\xc3\x82',
         '&#195;': '\xc3\x83',
         '&Atilde;': '\xc3\x83',
         '&#196;': '\xc3\x84',
         '&Auml;': '\xc3\x84',
         '&#197;': '\xc3\x85',
         '&Aring;': '\xc3\x85',
         '&#198;': '\xc3\x86',
         '&AElig;': '\xc3\x86',
         '&#199;': '\xc3\x87',
         '&Ccedil;': '\xc3\x87',
         '&#200;': '\xc3\x88',
         '&Egrave;': '\xc3\x88',
         '&#201;': '\xc3\x89',
         '&Eacute;': '\xc3\x89',
         '&#202;': '\xc3\x8a',
         '&Ecirc;': '\xc3\x8a',
         '&#203;': '\xc3\x8b',
         '&Euml;': '\xc3\x8b',
         '&#204;': '\xc3\x8c',
         '&Igrave;': '\xc3\x8c',
         '&#205;': '\xc3\x8d',
         '&Iacute;': '\xc3\x8d',
         '&#206;': '\xc3\x8e',
         '&Icirc;': '\xc3\x8e',
         '&#207;': '\xc3\x8f',
         '&Iuml;': '\xc3\x8f',
         '&#208;': '\xc3\x90',
         '&ETH;': '\xc3\x90',
         '&#209;': '\xc3\x91',
         '&Ntilde;': '\xc3\x91',
         '&#210;': '\xc3\x92',
         '&Ograve;': '\xc3\x92',
         '&#211;': '\xc3\x93',
         '&Oacute;': '\xc3\x93',
         '&#212;': '\xc3\x94',
         '&Ocirc;': '\xc3\x94',
         '&#213;': '\xc3\x95',
         '&Otilde;': '\xc3\x95',
         '&#214;': '\xc3\x96',
         '&Ouml;': '\xc3\x96',
         '&#215;': '\xc3\x97',
         '&times;': '\xc3\x97',
         '&#216;': '\xc3\x98',
         '&Oslash;': '\xc3\x98',
         '&#217;': '\xc3\x99',
         '&Ugrave;': '\xc3\x99',
         '&#218;': '\xc3\x9a',
         '&Uacute;': '\xc3\x9a',
         '&#219;': '\xc3\x9b',
         '&Ucirc;': '\xc3\x9b',
         '&#220;': '\xc3\x9c',
         '&Uuml;': '\xc3\x9c',
         '&#221;': '\xc3\x9d',
         '&Yacute;': '\xc3\x9d',
         '&#222;': '\xc3\x9e',
         '&THORN;': '\xc3\x9e',
         '&#223;': '\xc3\x9f',
         '&szlig;': '\xc3\x9f',
         '&#224;': '\xc3\xa0',
         '&agrave;': '\xc3\xa0',
         '&#225;': '\xc3\xa1',
         '&aacute;': '\xc3\xa1',
         '&#226;': '\xc3\xa2',
         '&acirc;': '\xc3\xa2',
         '&#227;': '\xc3\xa3',
         '&atilde;': '\xc3\xa3',
         '&#228;': '\xc3\xa4',
         '&auml;': '\xc3\xa4',
         '&#229;': '\xc3\xa5',
         '&aring;': '\xc3\xa5',
         '&#230;': '\xc3\xa6',
         '&aelig;': '\xc3\xa6',
         '&#231;': '\xc3\xa7',
         '&ccedil;': '\xc3\xa7',
         '&#232;': '\xc3\xa8',
         '&egrave;': '\xc3\xa8',
         '&#233;': '\xc3\xa9',
         '&eacute;': '\xc3\xa9',
         '&#234;': '\xc3\xaa',
         '&ecirc;': '\xc3\xaa',
         '&#235;': '\xc3\xab',
         '&euml;': '\xc3\xab',
         '&#236;': '\xc3\xac',
         '&igrave;': '\xc3\xac',
         '&#237;': '\xc3\xad',
         '&iacute;': '\xc3\xad',
         '&#238;': '\xc3\xae',
         '&icirc;': '\xc3\xae',
         '&#239;': '\xc3\xaf',
         '&iuml;': '\xc3\xaf',
         '&#240;': '\xc3\xb0',
         '&eth;': '\xc3\xb0',
         '&#241;': '\xc3\xb1',
         '&ntilde;': '\xc3\xb1',
         '&#242;': '\xc3\xb2',
         '&ograve;': '\xc3\xb2',
         '&#243;': '\xc3\xb3',
         '&oacute;': '\xc3\xb3',
         '&#244;': '\xc3\xb4',
         '&ocirc;': '\xc3\xb4',
         '&#245;': '\xc3\xb5',
         '&otilde;': '\xc3\xb5',
         '&#246;': '\xc3\xb6',
         '&ouml;': '\xc3\xb6',
         '&#247;': '\xc3\xb7',
         '&divide;': '\xc3\xb7',
         '&#248;': '\xc3\xb8',
         '&oslash;': '\xc3\xb8',
         '&#249;': '\xc3\xb9',
         '&ugrave;': '\xc3\xb9',
         '&#250;': '\xc3\xba',
         '&uacute;': '\xc3\xba',
         '&#251;': '\xc3\xbb',
         '&ucirc;': '\xc3\xbb',
         '&#252;': '\xc3\xbc',
         '&uuml;': '\xc3\xbc',
         '&#253;': '\xc3\xbd',
         '&yacute;': '\xc3\xbd',
         '&#254;': '\xc3\xbe',
         '&thorn;': '\xc3\xbe',
         '&#255;': '\xc3\xbf',
         '&yuml;': '\xc3\xbf',
         '&#133;': '...',
         '&#151;': '-',
         '<br><br>': ' ',
         '<br />': '',
         '\r': '',
         '\n': '',
         '  ': ' '}
        for i in range(len(symbols_to_remove)):
            processingstring = string.replace(processingstring, symbols_to_remove.items()[i][0], symbols_to_remove.items()[i][1])

        return processingstring
    except:
        return ''


def singleValue(content, matchstring):
    result = ''
    matchstring = unicode(matchstring, 'utf8')
    regexp = re.compile(matchstring, re.DOTALL)
    result = regexp.search(content)
    if result != None:
        result = result.group(1)
        return result
    else:
        return ''


def multiValue(content, matchstring, matchstring2):
    result = ''
    matchstring = unicode(matchstring, 'utf8')
    matchstring2 = unicode(matchstring2, 'utf8')
    regexp = re.compile(matchstring, re.DOTALL)
    result = regexp.search(content)
    regexp = re.compile(matchstring2, re.DOTALL)
    result = regexp.finditer(result.group(0))
    j = 0
    retList = []
    for i in result:
        if i.group(1):
            retList.append(i.group(1))
        else:
            retList.append(i.group(0))
        j += 1

    result = retList
    return result


def search_title(title):
    title = title.decode('utf8')
    print title
    url = 'http://s.kinopoisk.ru/index.php?first=no&kp_query=' + title.encode('cp1251')
    watchrequest = Request(url, None, std_headers)
    try:
        watchvideopage = urlopen2(watchrequest)
    except (URLError, HTTPException, socket.error) as err:
        print '[Kinopoisk] Error: Unable to retrieve page - Error code: ', str(err)

    content = watchvideopage.read().decode('cp1251')
    watchvideopage.close()
    search_results = []
    content_results = content[content.find('\xd0\xa1\xd0\xba\xd0\xbe\xd1\x80\xd0\xb5\xd0\xb5 \xd0\xb2\xd1\x81\xd0\xb5\xd0\xb3\xd0\xbe, \xd0\xb2\xd1\x8b \xd0\xb8\xd1\x89\xd0\xb5\xd1\x82\xd0\xb5'):content.find('\xd0\x9d\xd0\xb0\xd0\xb9\xd0\xb4\xd0\xb5\xd0\xbd\xd0\xbd\xd1\x8b\xd0\xb5 \xd0\xb8\xd0\xbc\xd0\xb5\xd0\xbd\xd0\xb0')]
    if content_results:
        soup_results = BeautifulSoup(content_results)
        #print soup_results.prettify()
        result = soup_results.findAll('div', attrs={'class': re.compile('element')})
        results = '%s' % result
        yearitems = re.compile('<span class="year">(.*?)</span>').findall(results)
        titleitems = re.compile('<p class="name"><a href="/level/1/film/.*?sr/1/">(.*?)</a>').findall(results)
        iditems = re.compile('<p class="name"><a href="/level/1/film/(.*?)/sr/1/">').findall(results)
        for titleitem in titleitems:
            search_results.append(normilize_string(titleitem.encode('utf-8')))

        i = 0
        for yearitem in yearitems:
            if i < len(yearitems):
                search_results[i] = search_results[i] + '(' + yearitem.encode('utf-8') + ' \xd0\xb3\xd0\xbe\xd0\xb4)'
            i += 1

        r = 0
        l = 0
        for iditem in iditems:
            if l < len(iditems):
                search_results[l] = search_results[l] + ' ,' + 'id:' + iditem.encode('utf-8')
            l += 1
    return search_results


def search_data(id):
    url = 'http://www.kinopoisk.ru/level/1/film/' + id
    watchrequest = Request(url, None, std_headers)
    try:
        watchvideopage = urlopen2(watchrequest)
    except (URLError, HTTPException, socket.error) as err:
        print '[Kinopoisk] Error: Unable to retrieve page - Error code: ', str(err)

    data = watchvideopage.read().decode('cp1251')
    watchvideopage.close()
    content_results = '%s' % data
    try:
        filmdata = {'title': '',
         'countries': '',
         'year': '',
         'directors': '',
         'cast': '',
         'genre': '',
         'user_rating': '',
         'rating_count': '',
         'movie_rating': '',
         'plot': '',
         'runtime': ''}
        try:
            filmdata['title'] = normilize_string(singleValue(data, '<h1 class="moviename-big" itemprop="name">(.*?)</h1>'))
        except:
            filmdata['title'] = ''
        try:
            filmdata['directors'] = normilize_string(','.join(multiValue(data, '<tr><td class="type">\xd1\x80\xd0\xb5\xd0\xb6\xd0\xb8\xd1\x81\xd1\x81\xd0\xb5\xd1\x80</td>(.*?)</tr>', '<a href=".*?>(.*?)</a>')))
        except:
            filmdata['directors'] = ''
        try:
            filmdata['countries'] = ','.join(multiValue(data, '<td class="type"   >\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd0\xbd\xd0\xb0</td>(.*?)</tr>', '<a href=".*?>(.*?)</a>'))
        except:
            filmdata['countries'] = ''
        try:
            filmdata['year'] = singleValue(data, '<td class="type"   >\xd0\xb3\xd0\xbe\xd0\xb4</td>.*?<a href=.*?>(.*?)</a>')
        except:
            filmdata['year'] = ''
        try:
            filmdata['genre'] = ','.join(multiValue(data, '<tr><td class="type">\xd0\xb6\xd0\xb0\xd0\xbd\xd1\x80</td>(.*?)</tr>', '<a href=".*?>(.*?)</a>'))
        except:
            filmdata['genre'] = ''
        try:
            filmdata['user_rating'] = singleValue(data, '<div class="div1"><meta itemprop="ratingValue" content="(.*?)" />')
        except:
            filmdata['user_rating'] = ''
        try:
            filmdata['rating_count'] = normilize_string(singleValue(data, '<span class="ratingCount" itemprop="ratingCount">(.*?)</span>'))
        except:
            filmdata['rating_count'] = ''
        try:
            filmdata['plot'] = normilize_string(singleValue(data, '<tr><td colspan=3 style="padding: 10px.*?description">(.*?)</div></span>'))
        except:
            filmdata['plot'] = ''
        try:
            runtime = string.split(singleValue(data, '<td class="time" id="runtime">(.*?)</td>'))
            filmdata['runtime'] = runtime[0]
        except:
            filmdata['runtime'] = ''
        try:
            filmdata['cast'] = normilize_string(','.join(multiValue(data, '<div id="actorList" class="clearfix  ">(.*?)<li itemprop="actors"><a href="/film/.*?>...</a></li>', '<a href="/name.*? itemprop="name">(.*?)</a>')))
        except:
            filmdata['cast'] = ''
        try:
            movierating = string.split(singleValue(data, '<td class="type">\xd1\x80\xd0\xb5\xd0\xb9\xd1\x82\xd0\xb8\xd0\xbd\xd0\xb3 MPAA</td>.*?<img src.*?alt=(.*?) border=0>'))
            if len(movierating) > 0:
                filmdata['movie_rating'] = movierating[1]
            else:
                filmdata['movie_rating'] = ''
        except:
            filmdata['movie_rating'] = ''

        return filmdata

    except:
        print_exception(traceback.format_exc())
