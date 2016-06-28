'''
Copyright (C) 2012-2015  Diego Torres Milano
Created on Dec 1, 2012

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Diego Torres Milano
'''

__version__ = '0.0.1'
__origin_version__ = '10.3.4'

import sys
import warnings
import string
import datetime
import requests
if sys.executable:
    if 'monkeyrunner' in sys.executable:
        warnings.warn(
    '''

    You should use a 'python' interpreter, not 'monkeyrunner' for this module

    ''', RuntimeWarning)
import socket
import time
import re
import signal
import os
import types
import platform
import bunch


DEBUG = False
DEBUG_TOUCH = DEBUG and False
DEBUG_LOG = DEBUG and False
DEBUG_WINDOWS = DEBUG and False
DEBUG_COORDS = DEBUG and False

try:
    HOSTNAME = os.environ['ANDROID_ADB_SERVER_HOST']
except:
    HOSTNAME = '127.0.0.1'

try:
    PORT = int(os.environ['ANDROID_ADB_SERVER_PORT'])
except KeyError:
    PORT = 5037

OKAY = 'OKAY'
FAIL = 'FAIL'

UP = 0
DOWN = 1
DOWN_AND_UP = 2

TIMEOUT = 15

WIFI_SERVICE = 'wifi'

# some device properties
VERSION_SDK_PROPERTY = 'ro.build.version.sdk'
VERSION_RELEASE_PROPERTY = 'ro.build.version.release'


class Device:
    @staticmethod
    def factory(_str):
        if DEBUG:
            print >> sys.stderr, "Device.factory(", _str, ")"
        values = _str.split(None, 2)
        if DEBUG:
            print >> sys.stderr, "values=", values
        return Device(*values)

    def __init__(self, serialno, status, qualifiers=None):
        self.serialno = serialno
        self.status = status
        self.qualifiers = qualifiers

    def __str__(self):
        return "<<<" + self.serialno + ", " + self.status + ", %s>>>" % self.qualifiers

class WifiManager:
    '''
    Simulates Android WifiManager.
    
    @see: http://developer.android.com/reference/android/net/wifi/WifiManager.html
    '''
    
    WIFI_STATE_DISABLING = 0
    WIFI_STATE_DISABLED = 1
    WIFI_STATE_ENABLING = 2
    WIFI_STATE_ENABLED = 3
    WIFI_STATE_UNKNOWN = 4
    
    WIFI_IS_ENABLED_RE = re.compile('Wi-Fi is enabled')
    WIFI_IS_DISABLED_RE = re.compile('Wi-Fi is disabled')
    
    def __init__(self, device):
        self.device = device
        
    def getWifiState(self):
        '''
        Gets the Wi-Fi enabled state.
        
        @return: One of WIFI_STATE_DISABLED, WIFI_STATE_DISABLING, WIFI_STATE_ENABLED, WIFI_STATE_ENABLING, WIFI_STATE_UNKNOWN
        '''
        
        result = self.device.shell('dumpsys wifi')
        if result:
            state = result.splitlines()[0]
            if self.WIFI_IS_ENABLED_RE.match(state):
                return self.WIFI_STATE_ENABLED
            elif self.WIFI_IS_DISABLED_RE.match(state):
                return self.WIFI_STATE_DISABLED
        print >> sys.stderr, "UNKNOWN WIFI STATE:", state
        return self.WIFI_STATE_UNKNOWN

class AdbClient:

    def __init__(self, serialno=None, hostname=HOSTNAME, port=PORT, settransport=True, reconnect=True, ignoreversioncheck=False, initDisplayProp=True):
        self.serialno = serialno
        self.hostname = hostname
        self.port = port


        self.build = {}
        ''' Build properties '''

        self.__displayInfo = None

        self.display = {}

        if settransport and serialno != None:
            self.build[VERSION_SDK_PROPERTY] = int(self.__getProp(VERSION_SDK_PROPERTY))
            if initDisplayProp:
                self.initDisplayProperties()


    def setSerialno(self, serialno):
        if self.isTransportSet:
            raise ValueError("Transport is already set, serialno cannot be set once this is done.")
        self.serialno = serialno
        self.__setTransport()
        self.build[VERSION_SDK_PROPERTY] = int(self.__getProp(VERSION_SDK_PROPERTY))


    def getDevices(self):
        '''
        Use adb devices to get device list
        '''
        if DEBUG:
            print >> sys.stderr, "getDevices()"
        self.__send('host:devices-l', checkok=False)
        try:
        except RuntimeError, ex:
            print >> sys.stderr, "**ERROR:", ex
            return None
        devices = []
        for line in self.__receive().splitlines():
            devices.append(Device.factory(line))
        self.isTransportSet = False # FIXED by ssx
        return devices

    def shell(self, cmd=None):
        r = requests.post('localhost:7001/api/shell', data={'command': cmd})
        req = bunch.bunchify(r.json())
        # req.exit_code
        return req.output

    def __getRestrictedScreen(self):
        ''' Gets C{mRestrictedScreen} values from dumpsys. This is a method to obtain display dimensions '''

        rsRE = re.compile('\s*mRestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<w>\d+)x(?P<h>\d+)')
        for line in self.shell('dumpsys window').splitlines():
            m = rsRE.match(line)
            if m:
                return m.groups()
        raise RuntimeError("Couldn't find mRestrictedScreen in 'dumpsys window'")

    def getDisplayInfo(self):
        self.__checkTransport()
        displayInfo = self.getLogicalDisplayInfo()
        if displayInfo:
            return displayInfo
        displayInfo = self.getPhysicalDisplayInfo()
        self.__displayInfo = displayInfo  # add by gzliuxin 15/5/14
        if displayInfo:
            return displayInfo
        raise RuntimeError("Couldn't find display info in 'wm size', 'dumpsys display' or 'dumpsys window'")

    def getLogicalDisplayInfo(self):
        '''
        Gets C{mDefaultViewport} and then C{deviceWidth} and C{deviceHeight} values from dumpsys.
        This is a method to obtain display logical dimensions and density
        '''

        self.__checkTransport()
        logicalDisplayRE = re.compile('.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')
        for line in self.shell('dumpsys display').splitlines():
            m = logicalDisplayRE.search(line, 0)
            if m:
                self.__displayInfo = {}
                for prop in [ 'width', 'height', 'orientation' ]:
                    self.__displayInfo[prop] = int(m.group(prop))
                for prop in [ 'density' ]:
                    d = self.__getDisplayDensity(None, strip=True, invokeGetPhysicalDisplayIfNotFound=True)
                    if d:
                        self.__displayInfo[prop] = d
                    else:
                        # No available density information
                        self.__displayInfo[prop] = -1.0
                return self.__displayInfo
        return None

    def getPhysicalDisplayInfo(self):
        ''' Gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density'''

        self.__checkTransport()
        phyDispRE = re.compile('Physical size: (?P<width>)x(?P<height>).*Physical density: (?P<density>)', re.MULTILINE)
        m = phyDispRE.search(self.shell('wm size; wm density'))
        if m:
            displayInfo = {}
            for prop in [ 'width', 'height' ]:
                displayInfo[prop] = int(m.group(prop))
            for prop in [ 'density' ]:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        for line in self.shell('dumpsys display').splitlines():
            m = phyDispRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in [ 'width', 'height' ]:
                    displayInfo[prop] = int(m.group(prop))
                for prop in [ 'density' ]:
                    # In mPhysicalDisplayInfo density is already a factor, no need to calculate
                    displayInfo[prop] = float(m.group(prop))
                return displayInfo

        # This could also be mSystem or mOverscanScreen
        phyDispRE = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
        # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
        dispWHRE = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
        for line in self.shell('dumpsys window').splitlines():
            m = phyDispRE.search(line, 0)
            if not m:
                m = dispWHRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in [ 'width', 'height' ]:
                    displayInfo[prop] = int(m.group(prop))
                for prop in [ 'density' ]:
                    d = self.__getDisplayDensity(None, strip=True, invokeGetPhysicalDisplayIfNotFound=False)
                    if d:
                        displayInfo[prop] = d
                    else:
                        # No available density information
                        displayInfo[prop] = -1.0
                return displayInfo


    def __getProp(self, key, strip=True):
        if DEBUG:
            print >> sys.stderr, "__getProp(%s, %s)" % (key, strip)
        prop = self.shell('getprop %s' % key)
        if strip:
            prop = prop.rstrip('\r\n')
        if DEBUG:
            print >> sys.stderr, "    __getProp: returning '%s'" % prop
        return prop

    def __getDisplayWidth(self, key, strip=True):
        if self.__displayInfo and 'width' in self.__displayInfo:
            return self.__displayInfo['width']
        return self.getDisplayInfo()['width']

    def __getDisplayHeight(self, key, strip=True):
        if self.__displayInfo and 'height' in self.__displayInfo:
            return self.__displayInfo['height']
        return self.getDisplayInfo()['height']

    def __getDisplayOrientation(self, key, strip=True):
        """  orientation can be changed, so always get it again. by gzliuxin 15/5/14
        if self.__displayInfo and 'orientation' in self.__displayInfo:
            return self.__displayInfo['orientation']
        """
        displayInfo = self.getDisplayInfo()
        if 'orientation' in displayInfo:
            return displayInfo['orientation']
        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            return int(m.group(1))
        # We couldn't obtain the orientation
        return -1

    def __getDisplayDensity(self, key, strip=True, invokeGetPhysicalDisplayIfNotFound=True):
        if self.__displayInfo and 'density' in self.__displayInfo: # and self.__displayInfo['density'] != -1: # FIXME: need more testing
            return self.__displayInfo['density']
        BASE_DPI = 160.0
        d = self.getProperty('ro.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        d = self.getProperty('qemu.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        if invokeGetPhysicalDisplayIfNotFound:
            return self.getPhysicalDisplayInfo()['density']
        return -1.0

    def getSystemProperty(self, key, strip=True):
        self.__checkTransport()
        return self.getProperty(key, strip)

    def getProperty(self, key, strip=True):
        ''' Gets the property value for key '''

        self.__checkTransport()
        import collections
        MAP_PROPS = collections.OrderedDict([
                          (re.compile('display.width'), self.__getDisplayWidth),
                          (re.compile('display.height'), self.__getDisplayHeight),
                          (re.compile('display.density'), self.__getDisplayDensity),
                          (re.compile('display.orientation'), self.__getDisplayOrientation),
                          (re.compile('.*'), self.__getProp),
                          ])
        '''Maps properties key values (as regexps) to instance methods to obtain its values.'''

        for kre in MAP_PROPS.keys():
            if kre.match(key):
                return MAP_PROPS[kre](key=key, strip=strip)
        raise ValueError("key='%s' does not match any map entry")

    def getSdkVersion(self):
        '''
        Gets the SDK version.
        '''

        self.__checkTransport()
        return self.build[VERSION_SDK_PROPERTY]

    def press(self, name, eventType=DOWN_AND_UP):
        self.__checkTransport()
        if isinstance(name, unicode):
            name = name.decode('ascii', errors='replace')
        cmd = 'input keyevent %s' % name
        if DEBUG:
            print >> sys.stderr, "press(%s)" % cmd
        self.shell(cmd)

    def longPress(self, name, duration=0.5, dev='/dev/input/event0'):
        self.__checkTransport()
        # WORKAROUND:
        # Using 'input keyevent --longpress POWER' does not work correctly in
        # KitKat (API 19), it sends a short instead of a long press.
        # This uses the events instead, but it may vary from device to device.
        # The events sent are device dependent and may not work on other devices.
        # If this does not work on your device please do:
        #     $ adb shell getevent -l
        # and post the output to https://github.com/dtmilano/AndroidViewClient/issues
        # specifying the device and API level.
        if name[0:4] == 'KEY_':
            name = name[4:]
        if name in KEY_MAP:
            self.shell('sendevent %s 1 %d 1' % (dev, KEY_MAP[name]))
            self.shell('sendevent %s 0 0 0' % dev)
            time.sleep(duration)
            self.shell('sendevent %s 1 %d 0' % (dev, KEY_MAP[name]))
            self.shell('sendevent %s 0 0 0' % dev)
            return

        version = self.getSdkVersion()
        if version >= 19:
            cmd = 'input keyevent --longpress %s' % name
            if DEBUG:
                print >> sys.stderr, "longPress(%s)" % cmd
            self.shell(cmd)
        else:
            raise RuntimeError("longpress: not supported for API < 19 (version=%d)" % version)

    def startActivity(self, component=None, flags=None, uri=None):
        self.__checkTransport()
        cmd = 'am start'
        if component:
            cmd += ' -n %s' % component
        if flags:
            cmd += ' -f %s' % flags
        if uri:
            cmd += ' %s' % uri
        if DEBUG:
            print >> sys.stderr, "Starting activity: %s" % cmd
        out = self.shell(cmd)
        if re.search(r"(Error type)|(Error: )|(Cannot find 'App')", out, re.IGNORECASE | re.MULTILINE):
            raise RuntimeError(out)
        return out

    def takeSnapshot(self, reconnect=False):
        '''
        Takes a snapshot of the device and return it as a PIL Image.
        '''
        # FIXME(ssx): again
        pass

    def touch(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print >> sys.stderr, "touch(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")"
        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        self.shell('input tap %d %d' % self.__transformPointByOrientation((x, y), orientation, self.display['orientation']))

    def touchDip(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print >> sys.stderr, "touchDip(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")"
        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        x = x * self.display['density']
        y = y * self.display['density']
        self.touch(x, y, orientation, eventType)

    def longTouch(self, x, y, duration=2000, orientation=-1):
        '''
        Long touches at (x, y)
        
        @param duration: duration in ms
        @param orientation: the orientation (-1: undefined)

        This workaround was suggested by U{HaMi<http://stackoverflow.com/users/2571957/hami>}
        '''
        
        self.__checkTransport()
        self.drag((x, y), (x, y), duration, orientation)

    def drag(self, (x0, y0), (x1, y1), duration, steps=1, orientation=-1):
        '''
        Sends drag event n PX (actually it's using C{input swipe} command.

        @param (x0, y0): starting point in PX
        @param (x1, y1): ending point in PX
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by @{input swipe})
        @param orientation: the orientation (-1: undefined)
        '''

        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        (x0, y0) = self.__transformPointByOrientation((x0, y0), orientation, self.display['orientation'])
        (x1, y1) = self.__transformPointByOrientation((x1, y1), orientation, self.display['orientation'])

        version = self.getSdkVersion()
        if version <= 15:
            raise RuntimeError('drag: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))

    def dragDip(self, (x0, y0), (x1, y1), duration, steps=1, orientation=-1):
        '''
        Sends drag event in DIP (actually it's using C{input swipe} command.

        @param (x0, y0): starting point in DIP
        @param (x1, y1): ending point in DIP
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by @{input swipe}
        '''

        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        density = self.display['density'] if self.display['density'] > 0 else 1
        x0 = x0 * density
        y0 = y0 * density
        x1 = x1 * density
        y1 = y1 * density
        self.drag((x0, y0), (x1, y1), duration, steps, orientation)
        
    def type(self, text):
        self.__checkTransport()
        self.shell(u'input text "%s"' % text)

    def wake(self):
        self.__checkTransport()
        if not self.isScreenOn():
            self.shell('input keyevent POWER')

    def isLocked(self):
        '''
        Checks if the device screen is locked.

        @return True if the device screen is locked
        '''

        self.__checkTransport()
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen lock state")

    def isScreenOn(self):
        '''
        Checks if the screen is ON.

        @return True if the device screen is ON
        '''

        self.__checkTransport()
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen ON state")

    def unlock(self):
        '''
        Unlocks the screen of the device.
        '''

        self.__checkTransport()
        self.shell('input keyevent MENU')
        self.shell('input keyevent BACK')

    @staticmethod
    def percentSame(image1, image2):
        '''
        Returns the percent of pixels that are equal

        @author: catshoes
        '''

        # If the images differ in size, return 0% same.
        size_x1, size_y1 = image1.size
        size_x2, size_y2 = image2.size
        if (size_x1 != size_x2 or
            size_y1 != size_y2):
            return 0

        # Images are the same size
        # Return the percent of pixels that are equal.
        numPixelsSame = 0
        numPixelsTotal = size_x1 * size_y1
        image1Pixels = image1.load()
        image2Pixels = image2.load()

        # Loop over all pixels, comparing pixel in image1 to image2
        for x in range(size_x1):
            for y in range(size_y1):
                if (image1Pixels[x, y] == image2Pixels[x, y]):
                    numPixelsSame += 1

        return numPixelsSame / float(numPixelsTotal)

    @staticmethod
    def sameAs(image1, image2, percent=1.0):
        '''
        Compares 2 images

        @author: catshoes
        '''

        return (AdbClient.percentSame(image1, image2) >= percent)

    def isKeyboardShown(self):
        '''
        Whether the keyboard is displayed.
        '''

        self.__checkTransport()
        dim = self.shell('dumpsys input_method')
        if dim:
            # FIXME: API >= 15 ?
            return "mInputShown=true" in dim
        return False

    def initDisplayProperties(self):
        self.__checkTransport()
        self.__displayInfo = None
        self.display['width'] = self.getProperty('display.width')
        self.display['height'] = self.getProperty('display.height')
        self.display['density'] = self.getProperty('display.density')
        self.display['orientation'] = self.getProperty('display.orientation')
        
    def getSystemService(self, name):
        if name == WIFI_SERVICE:
            return WifiManager(self)

    def getTopActivityNameAndPid(self):
        dat = self.shell('dumpsys activity top')
        lines = dat.splitlines()
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(lines[1])
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            warnings.warn("NO MATCH:" + lines[1])
            return None

    def getTopActivityName(self):
        tanp = self.getTopActivityNameAndPid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

if __name__ == '__main__':
    adbClient = AdbClient(os.environ['ANDROID_SERIAL'])
    INTERACTIVE = True#False
    if INTERACTIVE:
        sout = adbClient.shell()
        prompt = re.compile(".+@android:(.*) [$#] \r\r\n")
        while True:
            try:
                cmd = raw_input('adb $ ')
            except EOFError:
                break
            if cmd == 'exit':
                break
            adbClient.socket.send(cmd + "\r\n")
            sout.readline(4096)  # eat first line, which is the command
            while True:
                line = sout.readline(4096)
                if prompt.match(line):
                    break
                print line,
                if not line:
                    break

        print "\nBye"
    else:
        print 'date:', adbClient.shell('date')
