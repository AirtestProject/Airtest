import requests
import platform
import ctypes
import os
import time
import sys
from functools import wraps
from airtest.core.ios.constant import DEFAULT_GOIOS_PATH
from airtest.utils.logger import get_logger
from airtest.utils.runcommand import run_background_with_pipe, runcommand, run_background, runcommand_with_json_output

LOGGING = get_logger(__name__)

platform_system = platform.system()
GOIOS_PATH = DEFAULT_GOIOS_PATH.get(platform_system)

def get_func_args(func, args, kwargs):
    if sys.version_info >= (3, 3):
        from inspect import signature
        sig = signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        return bound_args.arguments
    else:
        from inspect import getargspec
        arg_names = getargspec(func).args
        # 将位置参数转为字典
        args_dict = dict(zip(arg_names, args))
        # 合并关键字参数
        args_dict.update(kwargs)
        return args_dict


def check_tunnel():
    try:
        res = requests.get("http://127.0.0.1:60105/health")
        if res.status_code == 200:
            return True
    except Exception as e:
        return False
    

def get_tunnels():
    try:
        res = requests.get("http://127.0.0.1:60105/tunnels")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        return []
    

def get_tunnel_by_udid(udid):
    tunnels = get_tunnels()
    for tunnel in tunnels:
        if tunnel['udid'] == udid:
            return tunnel
    return None
    

def start_tunnel_service():
    if not GOIOS_PATH:
        return False
    
    if platform_system == "Windows":
        hinstance = ctypes.windll.shell32.ShellExecuteW(None, "runas", GOIOS_PATH, "tunnel start", os.path.dirname(GOIOS_PATH), 0)
    elif platform_system == "Darwin":
        password = os.environ.get("ADMIN_PASSWORD")
        if password:
            proc = run_background_with_pipe(["echo", password], ["sudo", "-S", GOIOS_PATH, "tunnel", "start"])
        else:
            raise Exception("Please set ADMIN_PASSWORD in os.environ.")

    time.sleep(5)
    if check_tunnel():
        return True
    else:
        return False


def decorator_checking_tunnel(func):
    """
    When the device is not paired, trigger the trust dialogue and try again.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        all_args = get_func_args(func, args, kwargs)
        udid = all_args.get('udid')

        if udid:
            major_version = GOIOSHelper.get_major_version(udid)
            if major_version < 17:
                return func(*args, **kwargs)

            if not check_tunnel():
                ret = start_tunnel_service()
                if not ret:
                    error_msg = f"Failed to start tunnel service. Please start tunnel service manually."
                    LOGGING.error(error_msg)
                    raise Exception(error_msg)

            cnt = 0
            tunnel = None
            while cnt < 3:
                tunnel = get_tunnel_by_udid(udid)
                if tunnel:
                    break
                cnt += 1
                time.sleep(1)
            if not tunnel:
                error_msg = f"Failed to get tunnel by udid: {udid} with major product version: {major_version}"
                LOGGING.error(error_msg)
                raise Exception(error_msg)

        return func(*args, **kwargs)
    return wrapper


class GOIOSHelper:
    """Below staticmethods are provided by GOIOS.
    TODO: 
    1. Enable developer mode. Now assume the developer mode is enabled.
    2. Mount specific image. Now image is mounted automatically by goios, while behaviors of some device models are not right with that image.
    """
    @staticmethod
    def devices():
        cmds = [GOIOS_PATH, "list"]
        res = runcommand_with_json_output(cmds)
        if res is None:
            return []
        else:
            return res["deviceList"]
        
    @staticmethod
    def device_info(udid):
        """
        Retrieves device information based on the provided UDID.

        Args:
            udid (str): The unique device identifier.

        Returns:
            dict: A dictionary containing selected device information. The keys include:
                - productVersion (str): The version of the product.
                - productType (str): The type of the product.
                - modelNumber (str): The model number of the device.
                - serialNumber (str): The serial number of the device.
                - phoneNumber (str): The phone number associated with the device.
                - timeZone (str): The time zone of the device.
                - uniqueDeviceID (str): The unique identifier of the device.
                - marketName (str): The market name of the device.

        """
        cmds = [GOIOS_PATH, f"--udid={udid}", "info"]
        goios_info = runcommand_with_json_output(cmds)
        if goios_info is None:
            return {}
        
        tmp_dict = {}
        # chose some useful device info from goios
        """
        'DeviceName', 'ProductVersion', 'ProductType',
        'ModelNumber', 'SerialNumber', 'PhoneNumber',
        'CPUArchitecture', 'ProductName', 'ProtocolVersion',
        'RegionInfo', 'TimeIntervalSince1970', 'TimeZone',
        'UniqueDeviceID', 'WiFiAddress', 'BluetoothAddress',
        'BasebandVersion'
        """
        for attr in ('ProductVersion', 'ProductType',
            'ModelNumber', 'SerialNumber', 'PhoneNumber', 
            'TimeZone', 'UniqueDeviceID'):
            if attr in goios_info:
                key = attr[0].lower() + attr[1:]
                tmp_dict[key] = goios_info[attr]

        tmp_dict["marketName"] = ""  # TODO: get marketName from goios
        return tmp_dict
    
    @staticmethod
    def get_major_version(udid):
        device_info = GOIOSHelper.device_info(udid)
        product_version = device_info.get('productVersion', '')
        return int(product_version.split('.')[0]) if product_version else 0

    @staticmethod
    @decorator_checking_tunnel
    def start_app(udid, bundle_id):
        cmds = [GOIOS_PATH, f"--udid={udid}", "launch", bundle_id]
        runcommand(cmds)

    @staticmethod
    @decorator_checking_tunnel
    def stop_app(udid, bundle_id):
        cmds = [GOIOS_PATH, f"--udid={udid}", "kill", bundle_id]
        runcommand(cmds)

    @staticmethod
    def get_app_list(udid, app_type="user"):
        cmds = [GOIOS_PATH, f"--udid={udid}", "apps"]
        if app_type == "system":
            cmds.append("--system")
        elif app_type == "all":
            cmds.append("--all")

        res = runcommand_with_json_output(cmds)
        return res if res is not None else []
    
    @staticmethod
    def list_wda(udid):
        """Get all WDA on device that meet certain naming rules.

        Returns:
            List of WDA bundleID.
        """
        app_list = GOIOSHelper.get_app_list(udid)
        wda_list = []
        for app in app_list:
            bundle_id = app["CFBundleIdentifier"]
            display_name = app["CFBundleDisplayName"]
            if (bundle_id.startswith('com.') and bundle_id.endswith(".xctrunner")) or display_name == "WebDriverAgentRunner-Runner":
                wda_list.append(bundle_id)
        return wda_list

    @staticmethod
    @decorator_checking_tunnel
    def ps(udid, only_user_app=True):
        """
        Retrieves the process list of the specified device.

        Parameters:
            udid (str): The unique device identifier.
            only_user_app (bool): Whether to only include processes of applications that are installed by user.

        Returns:
            list: A list of dictionaries containing information about each process. Each dictionary contains the following keys:
                - pid (int): The process ID.
                - name (str): The name of the process.
                - bundle_id (str): The bundle identifier of the process.
                - display_name (str): The display name of the process.
            e.g. [{'pid': 1, 'name': 'MobileSafari', 'bundle_id': 'com.apple.mobilesafari', 'display_name': 'Safari'}, ...]

        """
        cmds = [GOIOS_PATH, f"--udid={udid}", "ps"]
        if only_user_app:
            cmds.append("--apps")

        proc_list = runcommand_with_json_output(cmds)
        if proc_list is None:
            return []
        
        # 部分信息例如bundleid、display_name等，在ps命令中没有，需要通过apps命令获取
        app_list = GOIOSHelper.get_app_list(udid, app_type="all")

        def check_app_match(app_info, proc_info):
            exec_path = app_info['Path'] + "/" + app_info['CFBundleExecutable']
            if exec_path.startswith("/private"):
                exec_path = exec_path[len("/private"):]
            
            if proc_info.get("RealAppName", "") == exec_path:
                return True
            return False

        ps_list = []
        for p in proc_list:
            data = {
                "pid": p['Pid'],
                "name": p['Name']
            }
            app_info = next((app for app in app_list if check_app_match(app, p)), None)
            if app_info:
                data['bundle_id'] = app_info['CFBundleIdentifier']
                data['display_name'] = app_info['CFBundleDisplayName']
            ps_list.append(data)

        return ps_list

    
    @staticmethod
    @decorator_checking_tunnel
    def ps_wda(udid):
        """Get all running WDA on device that meet certain naming rules.

        Returns:
            List of running WDA bundleID.
        """
        ps_list = GOIOSHelper.ps(udid)
        ps_wda_list = []
        for p in ps_list:
            if "bundle_id" not in p and "display_name" not in p:
                continue

            if ".xctrunner" in p["bundle_id"] or p["display_name"] == "WebDriverAgentRunner-Runner":
                ps_wda_list.append(p["bundle_id"])
            else:
                continue
        return ps_wda_list
    
    @staticmethod
    @decorator_checking_tunnel
    def xctest(udid, wda_bundle_id):
        print(f"run xctest for {udid} with {wda_bundle_id} by goios")
        app_list = GOIOSHelper.get_app_list(udid)
        wda_app_info = next((app for app in app_list if app['CFBundleIdentifier'] == wda_bundle_id), None)
        if not wda_app_info:
            raise Exception(f"Failed to find {wda_bundle_id} in {udid}")
        
        exec_name = wda_app_info['CFBundleExecutable']
        xctestname = exec_name.replace("-Runner", "") + ".xctest"
        cmds = [GOIOS_PATH, f"--udid={udid}", "runwda", f"--bundleid={wda_bundle_id}", f"--testrunnerbundleid={wda_bundle_id}", f"--xctestconfig={xctestname}"]
        proc = run_background(cmds)
        time.sleep(3)
        if proc.poll() is None:
            return proc
