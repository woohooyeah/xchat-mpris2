#!/usr/bin/env python3
#

import xchat, dbus, os, inspect

__module_name__ = "xchat-mpris2" 
__module_version__ = "0.24"
__module_description__ = "Fetches information from MRPIS- and MPRIS2-compliant music players" 

bus = dbus.SessionBus()

player = "clementine"

def isPlayerSpecified():
  global player
  if player:
    return True
  return False

def status(str):
  xchat.prnt("[%s] %s" % (player, str))

# Pass in milliseconds, get (minutes, seconds)
def parseSongPosition(time):
  return getMinutesAndSeconds(time / 1000000)

# Pass in just seconds, get (minutes, seconds)
def getMinutesAndSeconds(seconds):
  return (seconds / 60, seconds % 60)

# Pass in both minutes and seconds
def formatTime(time):
  if time:
    return "%d:%02d" % time
  else:
    return "0:00"

def performAction(action):
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.mpris.MediaPlayer2.Player")
    
    fn = getattr(iface, action)
    if fn:
      return fn()
  except dbus.exceptions.DBusException:
    return False

def getProperty(interface, prop):
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Properties")
    
    return iface.Get(interface, prop)
  except dbus.exceptions.DBusException:
    return False

def getSongURLInfo():
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Properties")

    data = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")

    url = ""
    if "xesam:url" in data:
      url = data["xesam:url"]
    else:
      url = ""

    return url

  except dbus.exceptions.DBusException:
    return False

def getSongInfo():
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Properties")

    remote_object_mpris = bus.get_object("org.mpris.%s" % (player), "/Player")
    iface_mpris = dbus.Interface(remote_object_mpris, "org.freedesktop.MediaPlayer")
    data_mpris = iface_mpris.GetMetadata()
    
    data = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")

    artist = ""
    if "xesam:artist" in data:
      artist = data["xesam:artist"][0]

    title = ""
    if "xesam:title" in data:
      title = data["xesam:title"]

    album = ""
    if "xesam:album" in data:
      album = data["xesam:album"]

    year = ""
    if "year" in data_mpris:
      year = data_mpris["year"]

    bitrate = ""
    if "audio-bitrate" in data_mpris:
      bitrate = data_mpris["audio-bitrate"]

    samplingrate = ""
    if "audio-samplerate" in data_mpris:
      samplingrate = data_mpris["audio-samplerate"]

    pos = ""
    pos = getProperty("org.mpris.MediaPlayer2.Player", "Position")
    if not pos == 0:
      pos = formatTime(parseSongPosition(pos))
    else:
      pos = formatTime(0)

    length = ""
    if "mpris:length" in data:
      length = formatTime(parseSongPosition(data["mpris:length"]))
    #or we just assume it's a stream, because it _is_ playing
    else:
      length = "STREAM"

    if artist:
      s_artist = "\002" + str(artist) + "\002"
    else:
      s_artist = ""

    if title:
      s_title = "\002" + str(title) + "\002"
    else:
      s_title = ""

    if album:
      s_album = "\002\00304<\003\002" + str(album) + "\002\00304>\003\002 "
    else:
      s_album = ""

    if year:
      s_year = "\002\00307{\003\002" + str(year) + "\002\00307}\003\002 "
    else:
      s_year = ""

    if bitrate:
      s_bitrate = "\002\00308(\003\002" + str(bitrate) + "kbps" + "\002\00308)\003\002 "
    else:
      s_bitrate = ""

    if samplingrate:
      sr_conv = round(float(samplingrate / 1000), 1)
      s_samplingrate = "\002\00310<\003\002" + str(sr_conv) + "kHz" + "\002\00310>\003\002 "
    else:
      s_samplingrate = ""

    # Building the actual np line by merging all of the above:
    return (s_artist, s_title, s_album, s_year, s_bitrate, s_samplingrate,
      "\002\00306[\003\002" + str(pos) + "\002\00306/\003\002", str(length) + "\002\00306]\003\002")
    #else:
    #  return 0
  except dbus.exceptions.DBusException:
    return (False, False, False, False, False, False, False, False)

def mprisURLInfo(word, word_eol, userdata):
  if isPlayerSpecified():
    urlinfo = getSongURLInfo()
    if not urlinfo == False:
      xchat.command("ME is currently streaming from URL: %s" % urlinfo)
    else:
      xchat.prnt("Error in getSongURLInfo()")
  return xchat.EAT_ALL

def mprisNp(word, word_eol, userdata):
  if isPlayerSpecified():
    info = getSongInfo()
    if not info == False:
      xchat.command("ME is now playing: %s - %s %s%s%s%s%s%s" % info)
    else:
      xchat.prnt("Error in getSongInfo()")
  return xchat.EAT_ALL

def mprisPlayer(word, word_eol, userdata):
  global player
  if len(word) > 1:
    player = word[1]
    xchat.prnt("Media player set to \"%s\"" % player)
    return xchat.EAT_ALL
  else:
    pass
  xchat.prnt("USAGE: %s <player name>, set default meda player." % word[0])
  return xchat.EAT_ALL

def mprisPlay(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing')
      performAction('Play')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisPause(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Paused')
      performAction('Pause')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisStop(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Stopped')
      performAction('Stop')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisPrev(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing previous song.')
      performAction('Previous')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisNext(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing next song.')
      performAction('Next')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

if isPlayerSpecified():
  xchat.prnt("Current media player is %s" % player)

xchat.hook_command("PLAYER", mprisPlayer, help="Usage: PLAYER <player name>, set default player.\nDefaults to clementine initially, but can be changed (no idea why you should though).")
xchat.hook_command("NP",     mprisNp,     help="Usage: NP, send information on current song to the active channel.")
xchat.hook_command("NEXT",   mprisNext,   help="Usage: NEXT, play next song.")
xchat.hook_command("PREV",   mprisPrev,   help="Usage: PREV, play previous song.")
xchat.hook_command("PLAY",   mprisPlay,   help="Usage: PLAY, play the music.")
xchat.hook_command("PAUSE",  mprisPause,  help="Usage: PAUSE, pause the music.")
xchat.hook_command("STOP",   mprisStop,   help="Usage: STOP, hammer time!")
xchat.hook_command("URLINFO", mprisURLInfo,   help="Usage: URLINFO, where the streaming audio comes from.\nWARNING: shows a local path if the audio is not network-streamed.")

xchat.prnt("MPRIS2 now playing script initialized.")
xchat.prnt("Use /player <player name> to specify the media player you are using (defaults to clementine).")
xchat.prnt("Use /np to send information on the current song to the active channel.")
xchat.prnt("Also provides: /next, /prev, /play, /pause, /stop")
