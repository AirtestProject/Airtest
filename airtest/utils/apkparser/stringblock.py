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

import six
from .bytecode import SV


class StringBlock:
    """
    axml format translated from:
    http://code.google.com/p/android4me/source/browse/src/android/content/res/AXmlResourceParser.java
    """
    def __init__(self, buff):
        buff.read(4)

        self.chunkSize = SV('<L', buff.read(4))
        self.stringCount = SV('<L', buff.read(4))
        self.styleOffsetCount = SV('<L', buff.read(4))

        # unused value ?
        buff.read(4) # ?

        self.stringsOffset = SV('<L', buff.read(4))
        self.stylesOffset = SV('<L', buff.read(4))

        self.m_stringOffsets = []
        self.m_styleOffsets = []
        self.m_strings = []
        self.m_styles = []

        for i in range(0, self.stringCount.get_value()):
            self.m_stringOffsets.append(SV('<L', buff.read(4)))

        for i in range(0, self.styleOffsetCount.get_value()):
            self.m_stylesOffsets.append(SV('<L', buff.read(4)))

        size = self.chunkSize.get_value() - self.stringsOffset.get_value()
        if self.stylesOffset.get_value() != 0:
            size = self.stylesOffset.get_value() - self.stringsOffset.get_value()

        # FIXME
        if (size % 4) != 0:
            pass

        for i in range(0, int(size / 4)):
            self.m_strings.append(SV('=L', buff.read(4)))

        if self.stylesOffset.get_value() != 0:
            size = self.chunkSize.get_value() - self.stringsOffset.get_value()

            # FIXME
            if (size % 4) != 0:
                pass

            for i in range(0, size / 4):
                self.m_styles.append(SV('=L', buff.read(4)))

    def getRaw(self, idx):
        if idx < 0 or self.m_stringOffsets == [] or idx >= len(self.m_stringOffsets):
            return None

        offset = self.m_stringOffsets[ idx ].get_value()
        length = self.getShort(self.m_strings, offset)

        data = ""

        while length > 0:
            offset += 2
            # get the unicode character as the apk might contain non-ASCII label
            data += six.unichr(self.getShort(self.m_strings, offset))

            # FIXME
            if data[-1] == "&":
                data = data[:-1]

            length -= 1

        return data

    def getShort(self, array, offset):
        value = array[int(offset / 4)].get_value()
        if (int((offset % 4)) / 2) == 0:
            return value & 0xFFFF
        else:
            return value >> 16
