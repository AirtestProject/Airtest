# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.


from .axmlprinter import AXMLPrinter
import zipfile
from xml.dom import minidom


class APK:
    """APK manages apk file format"""
    def __init__(self, filename):
        """
            @param filename: specify the path of the file, or raw data
            @param raw: specify (boolean) if the filename is a path or raw data
        """
        self.filename = filename

        self.xml = {}
        self.package = ""
        self.androidversion = {}
        self._permissions = []
        self.valid_apk = False

        with open(filename, "rb") as fd:
            self.__raw = fd.read()

        self.zip = zipfile.ZipFile(filename)

        for i in self.zip.namelist():
            if i == "AndroidManifest.xml":
                self.xml[i] = minidom.parseString(AXMLPrinter(self.zip.read(i)).getBuff())

                self.package = self.xml[i].documentElement.getAttribute("package")
                self.androidversion["Code"] = self.xml[i].documentElement.getAttribute("android:versionCode")
                self.androidversion["Name"] = self.xml[i].documentElement.getAttribute("android:versionName")

                for item in self.xml[i].getElementsByTagName("uses-permission"):
                    self._permissions.append(str(item.getAttribute("android:name")))

                self.valid_apk = True

    def is_valid_apk(self):
        return self.valid_apk

    def get_filename(self):
        """
            Return the filename of the APK
        """
        return self.filename

    def get_package(self):
        """
            Return the name of the package
        """
        return self.package

    def get_androidversion_code(self):
        """
            Return the android version code
        """
        return self.androidversion["Code"]
    androidversion_code = property(get_androidversion_code)

    def get_androidversion_name(self):
        """
            Return the android version name
        """
        return self.androidversion["Name"]
    androidversion_name = property(get_androidversion_name)

    def get_files(self):
        """
            Return the files inside the APK
        """
        return self.zip.namelist()
    files = property(get_files)

    def get_files_types(self):
        """
            Return the files inside the APK with their types (by using python-magic)
        """
        try:
            import magic
        except ImportError:
            return {}

        l = {}

        builtin_magic = 0
        try:
            getattr(magic, "Magic")
        except AttributeError:
            builtin_magic = 1

        if builtin_magic:
            ms = magic.open(magic.MAGIC_NONE)
            ms.load()

            for i in self.get_files():
                l[ i ] = ms.buffer(self.zip.read(i))
        else:
            m = magic.Magic()
            for i in self.get_files():
                l[ i ] = m.from_buffer(self.zip.read(i))

        return l
    files_types = property(get_files_types)

    def get_raw(self):
        """
            Return raw bytes of the APK
        """
        return self.__raw
    raw = property(get_raw)

    def get_file(self, filename):
        """
            Return the raw data of the specified filename
        """
        try:
            return self.zip.read(filename)
        except KeyError:
            return ""

    def get_dex(self):
        """
            Return the raw data of the classes dex file
        """
        return self.get_file("classes.dex")
    dex = property(get_dex)

    def get_elements(self, tag_name, attribute):
        """
            Return elements in xml files which match with the tag name and the specific attribute

            @param tag_name: a string which specify the tag name
            @param attribute: a string which specify the attribute
        """
        l = []
        for i in self.xml:
            for item in self.xml[i].getElementsByTagName(tag_name):
                value = item.getAttribute(attribute)

                if len(value) > 0:
                    if value[0] == ".":
                        value = self.package + value
                    else:
                        v_dot = value.find(".")
                        if v_dot == 0:
                            value = self.package + "." + value
                        elif v_dot == -1:
                            value = self.package + "." + value

                l.append(str(value))
        return l

    def get_element(self, tag_name, attribute):
        """
            Return element in xml files which match with the tag name and the specific attribute

            @param tag_name: a string which specify the tag name
            @param attribute: a string which specify the attribute
        """
        l = []
        for i in self.xml:
            for item in self.xml[i].getElementsByTagName(tag_name):
                value = item.getAttribute(attribute)

                if len(value) > 0:
                    return value
        return None

    def get_activities(self):
        """
            Return the android:name attribute of all activities
        """
        return self.get_elements("activity", "android:name")
    activities = property(get_activities)

    def get_services(self):
        """
            Return the android:name attribute of all services
        """
        return self.get_elements("service", "android:name")
    services = property(get_services)

    def get_receivers(self):
        """
            Return the android:name attribute of all receivers
        """
        return self.get_elements("receiver", "android:name")
    receivers = property(get_receivers)

    def get_providers(self):
        """
            Return the android:name attribute of all providers
        """
        return self.get_elements("provider", "android:name")
    providers = property(get_providers)

    def get_permissions(self):
        """
            Return permissions
        """
        return self._permissions
    permissions = property(get_permissions)

    def get_min_sdk_version(self):
        """
            Return the android:minSdkVersion attribute
        """
        return self.get_element("uses-sdk", "android:minSdkVersion")
    min_sdk_version = property(get_min_sdk_version)

    def get_target_sdk_version(self):
        """
            Return the android:targetSdkVersion attribute
        """
        return self.get_element("uses-sdk", "android:targetSdkVersion")
    target_sdk_version = property(get_target_sdk_version)

    def get_libraries(self):
        """
            Return the android:name attributes for libraries
        """
        return self.get_elements("uses-library", "android:name")
    libraries = property(get_libraries)

    def show(self):
        print("FILES: ", self.get_files_types())

        print("ACTIVITIES: ", self.get_activities())
        print("SERVICES: ", self.get_services())
        print("RECEIVERS: ", self.get_receivers())
        print("PROVIDERS: ", self.get_providers())

