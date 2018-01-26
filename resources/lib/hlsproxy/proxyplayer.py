import xbmc
from resources.lib.modules import control


class ProxyPlayer(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self)

    def log(msg):
        control.log(msg)

    def onPlayBackStarted(self):
        self.log('Now im playing... %s' % url)
        self.stopPlaying.clear()

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        self.log("seting event in onPlayBackEnded ")
        self.stopPlaying.set()
        self.log("stop Event is SET")

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        self.log("seting event in onPlayBackStopped ")
        self.stopPlaying.set()
        self.log("stop Event is SET")