import os
import pathlib
import sys
import time
from functools import wraps
from airtest.utils.decorators import add_decorator_to_methods
from airtest.utils.runcommand import run_background
from airtest.core.error import AirtestError
from tidevice._usbmux import Usbmux
from tidevice._device import BaseDevice
from tidevice._proto import MODELS
from tidevice.exceptions import MuxError
from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


def decorator_pairing_dialog(func):
    """
    When the device is not paired, trigger the trust dialogue and try again.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MuxError:
            if sys.platform.startswith("win"):
                error_msg = "Device is not yet paired. Triggered the trust dialogue. Please accept and try again. (iTunes is required on Windows.) "
            else:
                error_msg = "Device is not yet paired. Triggered the trust dialogue. Please accept and try again."
            LOGGING.error(error_msg)
            raise
    return wrapper


def format_file_list(file_list):
    formatted_list = []
    for file in file_list:
        file_info = {
            'type': 'Directory' if file[0] == 'd' else 'File',
            'size': file[1],
            'last_modified': file[2].strftime('%Y-%m-%d %H:%M:%S'),
            'name': file[3]
        }
        formatted_list.append(file_info)
    
    return formatted_list


@add_decorator_to_methods(decorator_pairing_dialog)
class TIDevice:
    """Below staticmethods are provided by Tidevice.
    """

    @staticmethod
    def devices():
        """
        Get all available devices connected by USB, return a list of UDIDs.

        Returns:
            list: A list of UDIDs. 
            e.g. ['539c5fffb18f2be0bf7f771d68f7c327fb68d2d9']
        """
        return Usbmux().device_udid_list()
    
    @staticmethod
    def list_app(udid, app_type="user"):
        """
        Returns a list of installed applications on the device.

        Args:
            udid (str): The unique identifier of the device.
            app_type (str, optional): The type of applications to list. Defaults to "user".
                Possible values are "user", "system", or "all".

        Returns:
            list: A list of tuples containing the bundle ID, display name,
                and version of the installed applications.
            e.g. [('com.apple.mobilesafari', 'Safari', '8.0'), ...]
        """
        app_type = {
            "user": "User",
            "system": "System",
            "all": None,
        }.get(app_type.lower(), None)
        app_list = []
        for info in BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=app_type):
            bundle_id = info['CFBundleIdentifier']
            try:
                display_name = info['CFBundleDisplayName']
                version = info.get('CFBundleShortVersionString', '')
                app_list.append((bundle_id, display_name, version))
            except BrokenPipeError:
                break
        return app_list

    @staticmethod
    def list_wda(udid):
        """Get all WDA on device that meet certain naming rules.

        Returns:
            List of WDA bundleID.
        """
        app_list = TIDevice.list_app(udid)
        wda_list = []
        for app in app_list:
            bundle_id, display_name, _ = app
            if (bundle_id.startswith('com.') and bundle_id.endswith(".xctrunner")) or display_name == "WebDriverAgentRunner-Runner":
                wda_list.append(bundle_id)
        return wda_list
    
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
        device_info = BaseDevice(udid, Usbmux()).device_info()
        tmp_dict = {}
        # chose some useful device info from tidevice
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
            key = attr[0].lower() + attr[1:]
            if attr in device_info:
                tmp_dict[key] = device_info[attr]
        try:
            tmp_dict["marketName"] = MODELS.get(device_info['ProductType'])
        except:
            tmp_dict["marketName"] = ""
        return tmp_dict
    
    @staticmethod
    def get_major_version(udid):
        """
        Retrieves the major version of the iOS device.
        """
        device_info = BaseDevice(udid, Usbmux()).device_info()
        product_version = device_info.get('ProductVersion', '')
        return int(product_version.split('.')[0]) if product_version else 0
    
    @staticmethod
    def install_app(udid, file_or_url):
        BaseDevice(udid, Usbmux()).app_install(file_or_url)

    @staticmethod
    def uninstall_app(udid, bundle_id):
        BaseDevice(udid, Usbmux()).app_uninstall(bundle_id=bundle_id)

    @staticmethod
    def start_app(udid, bundle_id):
        BaseDevice(udid, Usbmux()).app_start(bundle_id=bundle_id)

    @staticmethod
    def stop_app(udid, bundle_id):
        # Note: seems not work.
        BaseDevice(udid, Usbmux()).app_stop(pid_or_name=bundle_id)

    @staticmethod
    def ps(udid):
        """
        Retrieves the process list of the specified device.

        Parameters:
            udid (str): The unique device identifier.

        Returns:
            list: A list of dictionaries containing information about each process. Each dictionary contains the following keys:
                - pid (int): The process ID.
                - name (str): The name of the process.
                - bundle_id (str): The bundle identifier of the process.
                - display_name (str): The display name of the process.
            e.g. [{'pid': 1, 'name': 'MobileSafari', 'bundle_id': 'com.apple.mobilesafari', 'display_name': 'Safari'}, ...]

        """
        with BaseDevice(udid, Usbmux()).connect_instruments() as ts:
            app_infos = list(BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=None))
            ps = list(ts.app_process_list(app_infos))
        ps_list = []
        keys = ['pid', 'name', 'bundle_id', 'display_name']
        for p in ps:
            if not p['isApplication']:
                continue
            ps_list.append({key: p[key] for key in keys})
        return ps_list
    
    @staticmethod
    def ps_wda(udid):
        """Get all running WDA on device that meet certain naming rules.

        Returns:
            List of running WDA bundleID.
        """
        with BaseDevice(udid, Usbmux()).connect_instruments() as ts:
            app_infos = list(BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=None))
            ps = list(ts.app_process_list(app_infos))
        ps_wda_list = []
        for p in ps:
            if not p['isApplication']:
                continue
            if ".xctrunner" in p['bundle_id'] or p['display_name'] == "WebDriverAgentRunner-Runner":
                ps_wda_list.append(p['bundle_id'])
            else:
                continue
        return ps_wda_list
    
    @staticmethod
    def xctest(udid, wda_bundle_id):
        """
        Only for ios<17.
        """
        cmds = ["tidevice", "-u", udid, "xctest", "-B", wda_bundle_id]
        proc = run_background(cmds)
        time.sleep(3)
        if proc.poll() is None:
            return proc
    
    @staticmethod
    def push(udid, local_path, device_path, bundle_id=None, timeout=None):
        """
        Pushes a file or a directory from the local machine to the iOS device.

        Args:
            udid (str): The UDID of the iOS device.
            device_path (str): The directory path on the iOS device where the file or directory will be pushed.
            local_path (str): The local path of the file or directory to be pushed.
            bundle_id (str, optional): The bundle ID of the app. If provided, the file or directory will be pushed to the app's sandbox container. Defaults to None.
            timeout (int, optional): The timeout in seconds for the remote device operation. Defaults to None.

        Examples:

                Push a file to the DCIM directory::

                    >>> TIDevice.push("00008020-001270842E88002E", "C:/Users/username/Pictures/photo.jpg", "/DCIM")
                    >>> TIDevice.push("00008020-001270842E88002E", "C:/Users/username/Pictures/photo.jpg", "/DCIM/photo.jpg")

                Push a directory to the Documents directory of the Keynote app::

                    >>> TIDevice.push("00008020-001270842E88002E", "C:/Users/username/test.key", "/Documents", "com.apple.Keynote")
                    >>> TIDevice.push("00008020-001270842E88002E", "C:/Users/username/test.key", "/Documents/test.key", "com.apple.Keynote")
        """
        try:
            if not os.path.exists(local_path):
                raise AirtestError(f"Local path {local_path} does not exist.")
            
            if bundle_id:
                sync = BaseDevice(udid, Usbmux()).app_sync(bundle_id)
            else:
                sync = BaseDevice(udid, Usbmux()).sync

            if device_path.endswith("/") or device_path.endswith("\\"):
                device_path = device_path[:-1]

            if os.path.isfile(local_path):
                file_name = os.path.basename(local_path)
                # 如果device_path有后缀则认为是文件，和本地文件名不一样视为需要重命名
                if not os.path.splitext(device_path)[1]:
                    if os.path.basename(device_path) != file_name:
                        device_path = os.path.join(device_path, file_name)
                device_path = device_path.replace("\\", "/")
                # Create the directory if it does not exist
                sync.mkdir(os.path.dirname(device_path))

                with open(local_path, "rb") as f:
                    content = f.read()
                    sync.push_content(device_path, content)
            elif os.path.isdir(local_path):
                device_path = os.path.join(device_path, os.path.basename(local_path))
                device_path = device_path.replace("\\", "/")
                sync.mkdir(device_path)
                for root, dirs, files in os.walk(local_path):
                    # 创建文件夹
                    for directory in dirs:
                        dir_path = os.path.join(root, directory)
                        relative_dir_path = os.path.relpath(dir_path, local_path)
                        device_dir_path = os.path.join(device_path, relative_dir_path)
                        device_dir_path = device_dir_path.replace("\\", "/")
                        sync.mkdir(device_dir_path)
                    # 上传文件
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, local_path)
                        device_file_path = os.path.join(device_path, relative_path)
                        device_file_path = device_file_path.replace("\\", "/")
                        with open(file_path, "rb") as f:
                            content = f.read()
                            sync.push_content(device_file_path, content)
            print(f"pushed {local_path} to {device_path}")
        except Exception as e:
            raise AirtestError(f"Failed to push {local_path} to {device_path}. If push a FILE, please check if there is a DIRECTORY with the same name already exists. If push a DIRECTORY, please check if there is a FILE with the same name already exists, and try again.")

    @staticmethod
    def pull(udid, device_path, local_path, bundle_id=None, timeout=None):
        """
        Pulls a file or directory from the iOS device to the local machine.

        Args:
            udid (str): The UDID of the iOS device.
            device_path (str): The path of the file or directory on the iOS device.
                               Remote devices can only be file paths. 
            local_path (str): The destination path on the local machine.
                              Remote devices can only be file paths. 
            bundle_id (str, optional): The bundle ID of the app. If provided, the file or directory will be pulled from the app's sandbox. Defaults to None.
            timeout (int, optional): The timeout in seconds for the remote device operation. Defaults to None.

            Examples:
                
                    Pull a file from the DCIM directory::
    
                        >>> TIDevice.pull("00008020-001270842E88002E", "/DCIM/photo.jpg", "C:/Users/username/Pictures/photo.jpg")
                        >>> TIDevice.pull("00008020-001270842E88002E", "/DCIM/photo.jpg", "C:/Users/username/Pictures")
    
                    Pull a directory from the Documents directory of the Keynote app::
    
                        >>> TIDevice.pull("00008020-001270842E88002E", "/Documents", "C:/Users/username/Documents", "com.apple.Keynote")
                        >>> TIDevice.pull("00008020-001270842E88002E", "/Documents", "C:/Users/username/Documents", "com.apple.Keynote")

        """
        try:
            if bundle_id:
                sync = BaseDevice(udid, Usbmux()).app_sync(bundle_id)
            else:
                sync = BaseDevice(udid, Usbmux()).sync

            if TIDevice.is_dir(udid, device_path, bundle_id):
                os.makedirs(local_path, exist_ok=True)
                
            src = pathlib.Path(device_path)
            dst = pathlib.Path(local_path)
            if dst.is_dir() and src.name and sync.stat(src).is_dir():
                dst = dst.joinpath(src.name)

            sync.pull(src, dst)
            print("pulled", src, "->", dst)
        except Exception as e:
            raise AirtestError(f"Failed to pull {device_path} to {local_path}.")

    @staticmethod
    def rm(udid, remote_path, bundle_id=None):
        """
        Removes a file or directory from the iOS device.

        Args:
            udid (str): The UDID of the iOS device.
            remote_path (str): The path of the file or directory on the iOS device.
            bundle_id (str, optional): The bundle ID of the app. If provided, the file or directory will be removed from the app's sandbox. Defaults to None.

        Examples:
            Remove a file from the DCIM directory::

                >>> TIDevice.rm("00008020-001270842E88002E", "/DCIM/photo.jpg")
                >>> TIDevice.rm("00008020-001270842E88002E", "/DCIM/photo.jpg", "com.apple.Photos")

            Remove a directory from the Documents directory of the Keynote app::

                >>> TIDevice.rm("00008020-001270842E88002E", "/Documents", "com.apple.Keynote")
        """
        def _check_status(status, path):
            if status == 0:
                print("removed", path)
            else:
                raise AirtestError(f"<{status.name} {status.value}> Failed to remove {path}")
        
        def _remove_folder(udid, folder_path, bundle_id):
            folder_path = folder_path.replace("\\", "/")
            for file_info in TIDevice.ls(udid, folder_path, bundle_id):
                if file_info['type'] == 'Directory':
                    _remove_folder(udid, os.path.join(folder_path, file_info['name']), bundle_id)
                else:
                    status = sync.remove(os.path.join(folder_path, file_info['name']))
                    _check_status(status, os.path.join(folder_path, file_info['name']))
            # remove the folder itself
            status = sync.remove(folder_path)
            _check_status(status, folder_path)
        
        if bundle_id:
            sync = BaseDevice(udid, Usbmux()).app_sync(bundle_id)
        else:
            sync = BaseDevice(udid, Usbmux()).sync
        
        if TIDevice.is_dir(udid, remote_path, bundle_id):
            if not remote_path.endswith("/"):
                remote_path += "/"
            _remove_folder(udid, remote_path, bundle_id)
        else:
            status = sync.remove(remote_path)
            _check_status(status, remote_path)

    @staticmethod
    def ls(udid, remote_path, bundle_id=None):
        """
        List files and directories in the specified path on the iOS device.

        Args:
            udid (str): The UDID of the iOS device.
            remote_path (str): The path on the iOS device.
            bundle_id (str, optional): The bundle ID of the app. Defaults to None.

        Returns:
            list: A list of files and directories in the specified path.

        Examples:

            List files and directories in the DCIM directory::

                >>> print(TIDevice.ls("00008020-001270842E88002E", "/DCIM"))
                [{'type': 'Directory', 'size': 96, 'last_modified': '2021-12-01 15:30:13', 'name': '100APPLE/'}, {'type': 'Directory', 'size': 96, 'last_modified': '2021-07-20 17:29:01', 'name': '.MISC/'}]

            List files and directories in the Documents directory of the Keynote app::

                >>> print(TIDevice.ls("00008020-001270842E88002E", "/Documents", "com.apple.Keynote"))
                [{'type': 'File', 'size': 302626, 'last_modified': '2024-06-25 11:25:25', 'name': '演示文稿.key'}]
        """
        try:
            file_list = []
            if bundle_id:
                sync = BaseDevice(udid, Usbmux()).app_sync(bundle_id)
            else:
                sync = BaseDevice(udid, Usbmux()).sync
            if remote_path.endswith("/") or remote_path.endswith("\\"):
                remote_path = remote_path[:-1]
            for file_info in sync.listdir_info(remote_path):
                filename = file_info.st_name
                if file_info.is_dir():
                    filename = filename + "/"
                file_list.append(['d' if file_info.is_dir() else '-', file_info.st_size, file_info.st_mtime, filename])
            file_list = format_file_list(file_list)
            return file_list
        except Exception as e:
            raise AirtestError(f"Failed to list files and directories in {remote_path}.")

    @staticmethod
    def mkdir(udid, remote_path, bundle_id=None):
        """
        Create a directory on the iOS device.

        Args:
            udid (str): The UDID of the iOS device.
            remote_path (str): The path of the directory to be created on the iOS device.
            bundle_id (str, optional): The bundle ID of the app. Defaults to None.
        
        Examples:
            Create a directory in the DCIM directory::

                >>> TIDevice.mkdir("00008020-001270842E88002E", "/DCIM/test")

            Create a directory in the Documents directory of the Keynote app::

                >>> TIDevice.mkdir("00008020-001270842E88002E", "/Documents/test", "com.apple.Keynote")

        """
        if bundle_id:
            sync = BaseDevice(udid, Usbmux()).app_sync(bundle_id)
        else:
            sync = BaseDevice(udid, Usbmux()).sync

        status = sync.mkdir(remote_path)
        if int(status) == 0:
            print("created", remote_path)
        else:
            raise AirtestError(f"<{status.name} {status.value}> Failed to create directory {remote_path}")

    @staticmethod
    def is_dir(udid, remote_path, bundle_id):
        """
        Check if the specified path on the iOS device is a directory.

        Args:
            udid (str): The UDID of the iOS device.
            remote_path (str): The path on the iOS device.
            bundle_id (str): The bundle ID of the app.
        
        Returns:
            bool: True if the path is a directory, False otherwise.
        
        Examples:
            Check if the DCIM directory is a directory::

                >>> TIDevice.is_dir("00008020-001270842E88002E", "/DCIM")
                True

            Check if the Documents directory of the Keynote app is a directory::

                >>> TIDevice.is_dir("00008020-001270842E88002E", "/Documents", "com.apple.Keynote")
                True
                >>> TIDevice.is_dir("00008020-001270842E88002E", "/Documents/test.key", "com.apple.Keynote")
                False
        """
        try:
            remote_path = remote_path.rstrip("\\/")
            remote_path_dir, remote_path_base = os.path.split(remote_path)
            file_info = TIDevice.ls(udid, remote_path_dir, bundle_id)
            for info in file_info:
                # Remove the trailing slash.
                if info['name'].endswith("/"):
                    info['name'] = info['name'][:-1]
                if info['name'] == f"{remote_path_base}":
                    return info['type'] == 'Directory'
        except Exception as e:
            raise AirtestError(f"Failed to check if {remote_path} is a directory. Please check the path exist and try again.")     

