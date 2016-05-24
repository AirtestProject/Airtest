#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import shlex
import subprocess
import plist
import imobiledevice

from ..error import MoaError, ICmdError
# import sys
# sys.path.append("..")
# from error import MoaError, ICmdError

LOCAL_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"DeviceSupport")
AFC_UPLOAD_PATH_PREFIX = "/private/var/mobile/Media"

def run_cmd(cmds,not_wait=False):
    print cmds
    if isinstance(cmds, basestring):
        cmds = shlex.split(cmds)
    else:
        cmds = list(cmds)

    proc = subprocess.Popen(cmds,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if not_wait:
        return proc

    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise ICmdError(stdout, stderr)
    return stdout

def list_all_udid():
    """list all udid of devices attached to this pc"""

    try:
        result = imobiledevice.get_device_list()
    except imobiledevice.iDeviceError:
        raise MoaError("get device list error")
    else:
        return result

def get_device(udid=None):
    """get ios device by udid"""

    if udid is not None:
        try:
            device = imobiledevice.iDevice(str(udid))
        except imobiledevice.iDeviceError:
            raise MoaError("no ios device with udid: %s" %str(udid))
    else:
        try:
            device = imobiledevice.iDevice()
        except imobiledevice.iDeviceError:
            raise MoaError("no ios devices")

    if device is None:
        raise MoaError("can't detect any ios devies")

    return device

def check_system_version(udid=None):
    """
    check ios system version of the device, return prefix of version
    example: system version is 9.2.x, return 9.2
    """

    device = get_device(udid)
    ld = imobiledevice.LockdownClient(device)
    try:
        version = str(ld.get_value(key='ProductVersion'))
    except LockdownError:
        raise MoaError("can't get ios system version of device")
    else:
        if not version:
            raise MoaError("can't get ios system version of device")
        else:
            pattern = re.compile("([0-9]\.[0-9])(\.[0-9])*")
            match_obj = pattern.search(version)
            if match_obj == None:
                raise MoaError("invalid versiona: %s" %version)
            else:
                version_pre = match_obj.group(1)
                return version_pre

def get_service_client(service_class,udid=None):
    """get the service client on device by service class"""
    
    device = get_device(udid)
    ld = imobiledevice.LockdownClient(device) # lockdown client wiil be expired very soon, so it should be created every time
    try:
        service_client = ld.get_service_client(service_class)
    except imobiledevice.LockdownError:
        raise MoaError("lockdown client can't get service client of %s" %service_class)
    except Exception:
        raise MoaError("%s is not a valid ios service class" %service_class)
    else:
        return service_client

def cleanup(ios_path,udid=None):
    """clean up the path on ios device"""

    afc = get_service_client(imobiledevice.AfcClient,udid=udid)
    afc.remove_path(ios_path)

def upload_file(local_filename, ios_path="IPATemp", ios_filename="tmp.ipa", udid=None):
    """
    upload local file to ios device
    local_filename: local file
    ios_path: upload local file to /private/var/mobile/Media/ios_path
    ios_filename: name of file uploaded to ios device
    udid: default is None, the first device listed
    return upload_file_path: the real path file has been uploaded to
    """

    try:
        local_stream = open(local_filename)
    except IOError:
        raise MoaError("afc upload file error, can't open local file: %s" %(local_filename))

    afc = get_service_client(imobiledevice.AfcClient,udid=udid)

    try:
        afc.get_file_info(ios_path)
    except imobiledevice.AfcError, e:
        if (e.code == 8): # AFC_E_OBJECT_NOT_FOUND
            afc.make_directory(ios_path)
        else:
            raise MoaError("afc error, error code %d"%e.code)
        

    upload_file_path = os.path.join(ios_path,ios_filename)

    try:
        testipa = afc.open(upload_file_path, mode="w+")
        testipa.write(local_stream.read())
        testipa.close()
    except IOError:
        raise MoaError("afc upload file error, write file %s failed" %ios_filename)

    return upload_file_path

def install_file(filename="IPATemp/tmp.ipa",udid=None):
    """
    install app
    filename: name of the ipa file uploaded to ios device
    udid: default is None, the first device listed
    """

    instproxy = get_service_client(imobiledevice.InstallationProxyClient,udid=udid)

    try:
        # upgrade if IPA exist, can save time
        instproxy.upgrade(filename, plist.Dict({})) # async install 
        #instproxy.install(filename, plist.Dict({}))
    except imobiledevice.InstallationProxyError:
        raise MoaError("install app %s failed" %filename)

def install_app(local_ipa_file, udid=None):
    """
    install app
    local_ipa_file: local file with suffix .ipa
    """

    upload_file_path = upload_file(local_ipa_file,udid=udid)
    install_file(filename=upload_file_path,udid=udid)

def uninstall_app(appid,udid=None):
    """uninstall app by appid"""

    is_installed = check_app_installed(appid,udid=udid)
    if is_installed:
        instproxy = get_service_client(imobiledevice.InstallationProxyClient,udid=udid)
        try:
            instproxy.uninstall(appid,plist.Dict({}))
        except imobiledevice.InstallationProxyError:
            raise MoaError("uninstall app %s error" %appid)

def browse_applist(app_type="Any",udid=None):
    """
    browse app installed on device
    app_type: Any, System or User
    udid: default is None, the first device listed
    """

    instproxy = get_service_client(imobiledevice.InstallationProxyClient,udid=udid)

    if app_type not in ["Any","System","User"]:
        raise MoaError("browse installed app error, no such app type: %s" %app_type)

    client_options = plist.Dict({
        "ApplicationType": app_type,
        "ReturnAttributes": plist.Array([
            "CFBundleIdentifier",
            "CFBundleExecutable",
            "Container",
        ]),
    })

    try:
        app_list = instproxy.browse(client_options)
        # app_list format:
        # app_list = [
        #     {"CFBundleIdentifier":"com.lqm.app1", "CFBundleExecutable":"App1","Container":"container1"},
        #     ...,
        # ]
    except imobiledevice.InstallationProxyError:
        raise MoaError("browse applist error")

    return app_list

def get_app_bin_path(appid, udid=None):
    """get the app bin path on device"""

    instproxy = get_service_client(imobiledevice.InstallationProxyClient,udid=udid)
    try:
        bin_path = instproxy.get_path_for_bundle_identifier(appid)
    except imobiledevice.InstallationProxyError:
        raise MoaError("get app %s's bin path error" %appid)

    return bin_path

def check_app_installed(appid,udid=None):
    """check if app has been installed on device"""

    app_list = browse_applist()
    isInstalled = False
    for app in app_list:
        if app['CFBundleIdentifier'] == appid:
            isInstalled = True
            break

    return isInstalled

def check_imagemount(udid=None):
    """
    check if DeveloperDiskImage.dmg has been mounted to ios device
    return: True or False
    """

    imagemounter = get_service_client(imobiledevice.MobileImageMounterClient,udid=udid)
    try:
        imageinfo = imagemounter.lookup_image('Developer')
    except imobiledevice.MobileImageMounterError:
        raise MoaError("check image mount error")

    if imageinfo is None:
        return False
    ret = imageinfo.get('ImagePresent')
    if ret == plist.Bool(True):
        return True
    else:
        return False

def image_mount(version,image_path=LOCAL_IMAGE_PATH,udid=None):
    """
    mount DeveloperDiskImage.dmg to ios device
    image_path: root path of version/DeveloperDiskImage.dmg, default is ./DeviceSupport
    """

    image_file = os.path.join(image_path,version,"DeveloperDiskImage.dmg")
    image_signature_file = os.path.join(image_path,version,"DeveloperDiskImage.dmg.signature")

    if not os.path.exists(image_file):
        raise MoaError("no DeveloperDiskImage file : %s" %image_file)

    if not os.path.exists(image_signature_file):
        raise MoaError("no DeveloperDiskImage signature file: %s "%image_file)

    # mount image using idevice cmd
    cmd = "ideviceimagemounter %s %s" %(image_file,image_signature_file)
    run_cmd(cmd)

def debugserver_client_handle_response(debugserver, response):
    """
    translate the response to result can be read by people
    debugserver: DebugServerClient object
    response: response from device after send a command
    """

    threadStopped = False

    if not response:
        result = None
    elif len(response) == 0:    # no data
        result = None
    elif response == "OK":      # Success
        result = response
    elif response[0] == 'O':    # stdout/stderr
        result = debugserver.decode_string(response[1:])
    elif response[0] == 'T':    # thread stopped information
        result = "Thread stopped. Details:\n%s\n" % response[1:]
        threadStopped = True
    elif response[0] == 'E':    # Error
        result = "ERROR: %s\n" % response[1:]
    elif response[0] == 'W':    # Warnning
        result = "WARNING: %s\n" % response[1:]
    else:
        result = "Unknown: %s" % response
    
    return result

def pre_command(app_bin_path, udid=None):
    """
    run pre command before run or stop an app
    """
    app_root = os.path.dirname(app_bin_path)

    debugserver = get_service_client(imobiledevice.DebugServerClient,udid=udid)

    with imobiledevice.DebugServerCommand("QSetLogging:bitmask=LOG_ALL|LOG_RNB_REMOTE|LOG_RNB_PACKETS") as cmd:
        response = debugserver.send_command(cmd)
        if response == None:
            raise MoaError("debugserver run app error, cmd is QSetLogging")
    time.sleep(1)

    with imobiledevice.DebugServerCommand("QSetMaxPacketSize:", 1, ["1024"]) as cmd:
        response = debugserver.send_command(cmd)
        if response == None:
            raise MoaError("debugserver run app error, cmd is QSetMaxPacketSize")
    time.sleep(1)

    with imobiledevice.DebugServerCommand("QSetWorkingDir:", 1, [app_root]) as cmd:
        response = debugserver.send_command(cmd)
        if response == None:
            raise MoaError("debugserver run app error, cmd is QSetWorkingDir")
    time.sleep(1)

    response = debugserver.set_argv(1, [app_bin_path])
    if response == None:
        raise MoaError("debugserver run app error, cmd is set_argv")
    time.sleep(2)

    with imobiledevice.DebugServerCommand("Hc0") as cmd:
        response = debugserver.send_command(cmd)
        if response == None:
            raise MoaError("debugserver run app error, cmd is Hc0")
    time.sleep(2)

    return debugserver

def debugserver_run_app(app_bin_path, udid=None):
    """
    run app
    app_bin_path: app path on device
    """

    debugserver = pre_command(app_bin_path, udid=udid)
    # If return "Efailed to get the task for process XXX",
    #   add "get-task-allow = True" in entitlements.plist
    with imobiledevice.DebugServerCommand("qLaunchSuccess") as cmd:
        response = debugserver.send_command(cmd)
        if response == None:
            raise MoaError("debugserver run app error, cmd is qLaunchSuccess")
    time.sleep(2)

    with imobiledevice.DebugServerCommand("c") as cmd:
        response = debugserver.send_command(cmd)
        result = debugserver_client_handle_response(debugserver,response)

    # check if run succeed
    run_succeed = False
    start_time = time.time()
    run_timeout = 10  # check if the app can run succeed and last run_timeout seconds
    while True:
        with imobiledevice.DebugServerCommand("OK") as cmd:
            response = debugserver.send_command(cmd)

        if len(response)>0 and response[0]=='T':
            raise MoaError("debugserver run app error, thread stopped between %ds" %run_timeout)

        result = debugserver_client_handle_response(debugserver, response)
        time.sleep(1)

        if run_timeout is not None and run_timeout > 0 and time.time()-start_time > run_timeout: # succeed
            run_succeed = True
            break

def debugserver_stop_app(app_bin_path, udid=None):
    debugserver = pre_command(app_bin_path, udid=udid)
    with DebugServerCommand("k") as cmd:
        response = debugserver.send_command(cmd)
        result = debugserver_client_handle_response(debugserver, response)

def check_before_debugserver_run(appid,udid=None):
    """
    1. check if the app has been installed on device
    2. check if image has been mounted to device
    3. return: app bin path 
    """

    check_app_installed(appid,udid=udid)
    is_mounted = check_imagemount(udid=udid)
    if not is_mounted:
        version = check_system_version(udid)
        image_mount(version,udid=udid)
    app_bin_path = get_app_bin_path(appid,udid=udid)
    return app_bin_path

def launch_app(appid,udid=None):
    """launch an app"""

    app_bin_path = check_before_debugserver_run(appid,udid=udid)
    debugserver_run_app(app_bin_path,udid=udid)

def stop_app(appid,udid=None):
    """stop an app"""

    app_bin_path = check_before_debugserver_run(appid, udid=udid)
    debugserver_stop_app(app_bin_path,udid=udid)

def screenshot(udid=None):
    """
    screenshot on device
    return: screen datas
    """

    ssclient = get_service_client(imobiledevice.ScreenshotrClient, udid=udid)
    try:
        datas = ssclient.take_screenshot()
    except imobiledevice.ScreenshotrError:
        raise MoaError("take screenshot error")
    else:
        return datas

def get_orientation(udid=None):
    """
    get interface orientation of device
    return: orientation code like following                      IOS    Android
        SBSERVICES_INTERFACE_ORIENTATION_UNKNOWN                = 0        /
        SBSERVICES_INTERFACE_ORIENTATION_PORTRAIT               = 1        0
        SBSERVICES_INTERFACE_ORIENTATION_PORTRAIT_UPSIDE_DOWN   = 2        2
        SBSERVICES_INTERFACE_ORIENTATION_LANDSCAPE_RIGHT        = 3        1
        SBSERVICES_INTERFACE_ORIENTATION_LANDSCAPE_LEFT         = 4        3
    """

    sbclient = get_service_client(imobiledevice.SpringboardServicesClient, udid=None)
    try:
        orientation = sbclient.get_orientation()
    except imobiledevice.SpringboardServicesError:
        raise MoaError("get interface orientation error")
    else:
        if orientation == 0: # unknown
            raise MoaError("get interface orientation: unknown")

        # adjust to code used on android device
        if orientation == 1:
            return 0
        elif orientation == 2:
            return 2
        elif orientation == 3:
            return 1
        elif orientation == 4:
            return 3

def test():

    # install app test
    # upload_file_path = upload_file(new_ipaname,ios_path="IPATemp")
    # install_file(upload_file_path)

    # DeveloperDiskImage mounter test
    # index = 0
    # while not check_imagemount():
    #     index += 1
    #     if index > 5:
    #         break
    #     print "attempt: ",index
    #     version = check_system_version()
    #     image_mount(version)
    # debugserver = get_service_client(imobiledevice.DebugServerClient)
    # launch_app("com.lqm.PerformDetector")
    # stop_app("com.lqm.PerformDetector")

    # launch app test
    launch_app("com.netease.devtest")
    # launch_app("com.lqm.PerformDetector")
    # datas = screenshot()
    # try:
    #     open('tmp.png','wb').write(datas)
    # except IOError:
    #     print "write tmp.png error"

    pass

if __name__ == '__main__':
    test()
