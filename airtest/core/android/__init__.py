from android import ADB, Minicap, Minitouch, Android

try:
    from emulator.emulator import Emulator
except ImportError as e:
    Emulator = None
    # print "Emulator module available on Windows only: %s" % e.message