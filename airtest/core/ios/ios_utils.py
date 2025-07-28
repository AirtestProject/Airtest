import time
import wda
import wda.exceptions
import tidevice
from airtest.core.ios.goios_helper import GOIOSHelper
from airtest.core.ios.tidevice_helper import TIDevice
from airtest.core.error import WDAError, TIDeviceError, GOIOSError
    

def ios_list_devices():
    try:
        return TIDevice.devices()
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_get_device_info(udid):
    try:
        return TIDevice.device_info(udid)
    except Exception as e:
        raise TIDeviceError(e)


def ios_get_major_version(udid):
    try:
        return TIDevice.get_major_version(udid)
    except Exception as e:
        raise TIDeviceError(e)


def ios_list_app(udid, app_type="user"):
    try:
        return TIDevice.list_app(udid, app_type)
    except Exception as e:
        raise TIDeviceError(e)


def ios_list_wda(udid):
    try:
        return TIDevice.list_wda(udid)
    except wda.exceptions.MuxError as e:
        raise WDAError(e)
    except tidevice.exceptions.SocketError as e:
        raise TIDeviceError(e)


def ios_start_app(udid, bundle_id):
    try:
        return GOIOSHelper.start_app(udid, bundle_id)
    except Exception as e:
        raise GOIOSError(e)
    

def ios_stop_app(udid, bundle_id):
    try:
        return GOIOSHelper.stop_app(udid, bundle_id)
    except Exception as e:
        raise GOIOSError(e)
    

def ios_list_processes(udid):
    try:
        return GOIOSHelper.ps(udid)
    except Exception as e:
        raise GOIOSError(e)
    

def ios_list_processes_wda(udid):
    try:
        return GOIOSHelper.ps_wda(udid)
    except Exception as e:
        raise GOIOSError(e)
    

def ios_install_app(udid, file_or_url):
    try:
        return TIDevice.install_app(udid, file_or_url)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_uninstall_app(udid, bundle_id):
    try:
        return TIDevice.uninstall_app(udid, bundle_id)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_push(udid, local_path, remote_path, bundle_id=None, timeout=None):
    try:
        return TIDevice.push(udid, local_path, remote_path, bundle_id=bundle_id, timeout=timeout)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_pull(udid, remote_path, local_path, bundle_id=None, timeout=None):
    try:
        return TIDevice.pull(udid, remote_path, local_path, bundle_id=bundle_id, timeout=timeout)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_rm(udid, remote_path, bundle_id=None):
    try:
        return TIDevice.rm(udid, remote_path, bundle_id=bundle_id)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_ls(udid, remote_path, bundle_id=None):
    try:
        return TIDevice.ls(udid, remote_path, bundle_id=bundle_id)
    except Exception as e:
        raise TIDeviceError(e)

def ios_mkdir(udid, remote_path, bundle_id=None):
    try:
        return TIDevice.mkdir(udid, remote_path, bundle_id=bundle_id)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_is_dir(udid, remote_path, bundle_id=None):
    try:
        return TIDevice.is_dir(udid, remote_path, bundle_id=bundle_id)
    except Exception as e:
        raise TIDeviceError(e)
    

def ios_run_xctest(udid, wda_bundle_id):
    major_version = GOIOSHelper.get_major_version(udid)
    # 对于ios17以下的WDA，使用goios启动有时候会有问题，保留tidevice启动方式
    if major_version < 17:
        try:
            return TIDevice.xctest(udid, wda_bundle_id)
        except Exception as e:
            raise TIDeviceError(e)
    else:
        try:
            return GOIOSHelper.xctest(udid, wda_bundle_id)
        except Exception as e:
            raise GOIOSError(e)
        

def ios_launch_wda(udid, wda_bundle_id, force_start=False):
    def _check_wda_ready(udid):
        wda_client = wda.BaseClient(f"http+usbmux://{udid}:8100")
        if wda_client.is_ready():
            return True

    if not force_start:
        wda_status = _check_wda_ready(udid)
        if wda_status:
            return True

    try:
        GOIOSHelper.start_app(udid, wda_bundle_id)  # 先尝试用直接拉起wda的方式运行，如果不行再使用xctest方式
        time.sleep(2)
        wda_status = _check_wda_ready(udid)
        if wda_status:
            return True
    except Exception as e:
        pass

    ios_run_xctest(udid, wda_bundle_id)
    time.sleep(2)
    return _check_wda_ready(udid)
