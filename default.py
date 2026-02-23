# -*- coding: utf-8 -*-
import xbmcaddon,os,xbmcgui,re,xbmcplugin,json
from resources.lib import client
from resources.lib.utils import py2_encode

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
    from urllib.parse import parse_qsl
else:
    import urlparse
    from urllib import quote_plus
    from urlparse import parse_qsl

m4_url = 'https://www.m4sport.hu'
syshandle = int(sys.argv[1])

def root():
    addDir({'title': '[COLOR red]''[B]' + u'M4 \u00C9l\u0151' + '[/B][/COLOR]', 'action': 'getLive', 'streamid': 'mtv4live', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 1' +'[/COLOR]', 'action': 'getLive', 'streamid': 'extra', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 2' +'[/COLOR]', 'action': 'getLive', 'streamid': 'extra2', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 3' +'[/COLOR]', 'action': 'getLive', 'streamid': 'extra3', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 4' +'[/COLOR]', 'action': 'getLive', 'streamid': 'extra4', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 5' +'[/COLOR]', 'action': 'getLive', 'streamid': 'extra5', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 1' +'[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport1', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 2' +'[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport2', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 3' +'[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport3', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 4' +'[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport4', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 5' +'[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport5', 'isFolder': 'false'})

    categories = [ {'category': '1020', 
                   'title': u'Sporth\u00EDrek'},

                   {'category': '768',
                   'title': 'Magyar foci'},

                   {'category': '548',
                   'title': 'Boxutca',},

                   {'category': '1025',
                   'title': u'Sportk\u00F6zvet\u00EDt\u00E9sek'}]
    
    [i.update({'action': 'getEpisodes', 'page': '1', 'IsFolder': 'true'}) for i in categories]
    for i in categories:
        addDir(i)
    xbmcplugin.endOfDirectory(syshandle)


def getEpisodes():
    query = urlparse.urljoin(m4_url, '/wp-content/plugins/telesport.hu.widgets/widgets/newSubCategory/ajax_loadmore.php?cat_id={0}&post_type=video&blog_id=4&page_number={1}'.format(category, page))
    r = client.request(query)
    result = json.loads(r)
    for i in result:
        #if i['has_video'] != True: continue
        title = client.replaceHTMLCodes(i['title'])
        title = py2_encode(title)
        link = py2_encode(i['link'])
        if link.startswith('//'): link = 'http:' + link
        img = py2_encode(i['image'])
        if img.startswith('//'): img = 'http:' + img
        addDir({'title': title, 'url': link, 'action': 'getVideo', 'image': img, 'isFolder': 'false'})
    if len(result) >= 10:
        addDir({'title': '[COLOR green]Következő oldal[/COLOR]', 'action': 'getEpisodes', 'page': str(int(page) + 1), 'category': category, 'isFolder': 'true'})
    xbmcplugin.endOfDirectory(syshandle)

def is_dirty(candidate):
    blocklist = ['bumper', 'promo', 'advertisement', 'reklam']

    for word in blocklist:
        if word in candidate:
            return False
    return True

def get_depth(candidate):
    parsed = urlparse(candidate)
    path_segments = [segment for segment in parsed.path.split('/') if segment]

    return len(path_segments)


def getLive():
    content_id = streamid
    embeddedUrl = 'https://player.mediaklikk.hu/playernew/player.php?video={0}&noflash=yes&osfamily=Android&osversion=7.0&browsername=Chrome%20Mobile&browserversion=&title=&contentid={0}&embedded=1'.format(
        content_id)
    r = client.request(embeddedUrl)

    playlist = re.search('''['"]playlist['"]\s*:\s*(\[[^\]]+\])''', r)
    if playlist is None:
        ok = xbmcgui.Dialog().ok('Stream hiba',
                                 'A stream URL nem található. A válasz struktúra változhatott...')
        return  # fatal error

    playlist = json.loads(playlist.group(1))
    url_list = []
    for link_obj in playlist:
        url_str = link_obj.get('file', '')
        if '.m3u' in url_str:
            url_list.append(url_str) # sanitization; only introduce URLs that contain a stream link in the first place

    if len(url_list) == 0:
        raise ValueError("Nem találtunk stream URL-t!")

    link = None  # start with an invalid link

    # Primary structural check
    for link_candidate in url_list:
        if get_depth(link_candidate) > 4: continue  # skip if invalid url (typically banner streams like the one during
        # Olympic Games, have more slash separated segments. Valid URLS typically have 4 unless something changes
        link = link_candidate
        break  # always pick the first valid URL as they tend to be the first ones in the list (in play order)

    # if the aggressive filter yielded zero results, fall back to the word blocklist method
    if link is None:
        for link_candidate in url_list:
            if is_dirty(link_candidate): continue
            link = link_candidate
            break  # pick first valid

    # If none of these filters yielded any result then fall back to the first url and notify user
    if link is None:
        link = url_list[0]
        xbmcgui.Dialog().notification(
            'Stream figyelmeztetés',
            'Az URL filterek nem adtak eredményt, a legelső URL fog lejátszódni...',
            xbmcgui.NOTIFICATION_WARNING
        )

    if link.startswith('//'): link = 'http:' + link
    link = py2_encode(link)
    stream = get_Stream(link)
    if stream:
        resolve(stream, image, title)

def getVideo():
    r = client.request(url)
    token = re.search('[\'"]token[\'"]\s*:\s*[\'"]([^\'"]+)', r).group(1)
    m = client.request('http://player.mediaklikk.hu/playernew/player.php?video=' + token)
    link = re.search('"file"\s*:\s*"([^"]+)', m).group(1)
    link = link.replace('\\', '')
    if (not link.startswith("http:") or not link.startswith("https:")):
        link = "%s%s" % ("https:", link)
    stream = get_Stream(link)
    if stream:
        resolve(stream, image, title)
    else:
        return


def get_Stream(url):
    if xbmcaddon.Addon().getSetting('quality') == 'true':
        return url
    result = client.request(url)
    from resources.lib import m3u8_parser
    playlist = m3u8_parser.parse(result)['playlists']

    if not playlist:
        return url
    
    try: playlist = sorted(playlist, key=lambda tup: tup['stream_info']['bandwidth'], reverse=True)
    except: pass

    qkey = 'resolution' if 'resolution' in playlist[0]['stream_info'] else 'bandwidth'
    qualities = []
    urls = []

    for item in playlist:

        quality = str(item['stream_info'][qkey])
        uri = item['uri']
        uri = urlparse.urljoin(url, uri)
        qualities.append(quality)
        urls.append(uri)
    
    dialog = xbmcgui.Dialog()
    q = dialog.select('Minőség', qualities)
    if q <= len(qualities) and not q == -1:
        return(urls[q])
    else:
        return None


def resolve(url, icon, title):   
    item = xbmcgui.ListItem(path=url)
    item.setArt({'icon': icon, 'thumb': icon})
    item.setInfo(type='Video', infoLabels={'Title': title})
    xbmcplugin.setResolvedUrl(syshandle, True, item)


def addDir(item):
    sysimage = xbmcaddon.Addon().getAddonInfo('icon'); sysfanart = xbmcaddon.Addon().getAddonInfo('fanart')

    label = item['title']
    if 'image' in item:
        image = item['image']
    else:
        image = sysimage
    fanart = item['fanart'] if 'fanart' in item else sysfanart
    isFolder = False if 'isFolder' in item and not item['isFolder'] == 'true' else True
    url = '%s?action=%s' % (sys.argv[0], item['action'])
    try:
        url += '&title=%s' % quote_plus(item['title'])
    except KeyError:
        url += '&title=%s' % quote_plus(py2_encode(item['title']))
    try: url += '&url=%s' % quote_plus(item['url'])
    except: pass
    try: url += '&image=%s' % quote_plus(item['image'])
    except:pass
    try: url += '&category=%s' % quote_plus(item['category'])
    except: pass
    try: url += '&page=%s' % quote_plus(item['page'])
    except: pass
    try: url += '&streamid=%s' % quote_plus(item['streamid'])
    except: pass

    liz=xbmcgui.ListItem(label=label)
    liz.setArt({'icon': image, 'thumb': image, 'poster': image, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": label})
    if isFolder is False:
        liz.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=liz, isFolder=isFolder)


params = dict(parse_qsl(sys.argv[2].replace('?','')))

url = params.get("url")

title = params.get("title")

image = params.get("image")

action = params.get("action")

page = params.get("page")

category = params.get("category")

streamid = params.get("streamid", '')

if action==None:
    root()
elif action=='getEpisodes':
    getEpisodes()
elif action=='getVideo':
    getVideo()
elif action=='getLive':
    getLive()

