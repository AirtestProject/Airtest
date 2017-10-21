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

from . import typeconstants as tc
from .axmlparser import AXMLParser

from struct import pack, unpack
from xml.sax import saxutils


class AXMLPrinter:
    def __init__(self, raw_buff):
        self.axml = AXMLParser(raw_buff)
        self.xmlns = False

        self.buff = ""

        while 1:
            _type = self.axml.next()
            #print "tagtype = ", _type

            if _type == tc.START_DOCUMENT:
                self.buff += "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
            elif _type == tc.START_TAG:
                self.buff += "<%s%s\n" % (self.getPrefix(self.axml.getPrefix()), self.axml.getName())

                # FIXME: use namespace
                if self.xmlns == False:
                    self.buff += "xmlns:%s=\"%s\"\n" % (self.axml.getNamespacePrefix(0), self.axml.getNamespaceUri(0))
                    self.xmlns = True

                for i in range(0, self.axml.getAttributeCount()):
                    self.buff += "%s%s=\"%s\"\n" % (self.getPrefix(self.axml.getAttributePrefix(i)), self.axml.getAttributeName(i), self.getAttributeValue(i))

                self.buff += ">\n"

            elif _type == tc.END_TAG:
                self.buff += "</%s%s>\n" % (self.getPrefix(self.axml.getPrefix()), self.axml.getName())

            elif _type == tc.TEXT:
                self.buff += "%s\n" % self.axml.getText()

            elif _type == tc.END_DOCUMENT:
                break

    def getBuff(self):
        return self.buff.encode("utf-8")

    def getPrefix(self, prefix):
        if prefix == None or len(prefix) == 0:
            return ""

        return prefix + ":"

    def getAttributeValue(self, index):
        _type = self.axml.getAttributeValueType(index)
        _data = self.axml.getAttributeValueData(index)

        #print _type, _data
        if _type == tc.TYPE_STRING:
            return saxutils.escape(self.axml.getAttributeValue(index), entities={'"': '&quot;'})

        elif _type == tc.TYPE_ATTRIBUTE:
            return "?%s%08X" % (self.getPackage(_data), _data)

        elif _type == tc.TYPE_REFERENCE:
            return "@%s%08X" % (self.getPackage(_data), _data)

        # WIP
        elif _type == tc.TYPE_FLOAT:
            return "%f" % unpack("=f", pack("=L", _data))[0]

        elif _type == tc.TYPE_INT_HEX:
            return "0x%08X" % _data

        elif _type == tc.TYPE_INT_BOOLEAN:
            if _data == 0:
                return "false"
            return "true"

        elif _type == tc.TYPE_DIMENSION:
            return "%f%s" % (self.complexToFloat(_data), tc.DIMENSION_UNITS[_data & tc.COMPLEX_UNIT_MASK])

        elif _type == tc.TYPE_FRACTION:
            return "%f%s" % (self.complexToFloat(_data), tc.FRACTION_UNITS[_data & tc.COMPLEX_UNIT_MASK])

        elif _type >= tc.TYPE_FIRST_COLOR_INT and _type <= tc.TYPE_LAST_COLOR_INT:
            return "#%08X" % _data

        elif _type >= tc.TYPE_FIRST_INT and _type <= tc.TYPE_LAST_INT:
            if _data > 0x7fffffff:
                _data = (0x7fffffff & _data) - 0x80000000
                return "%d" % _data
            elif _type == tc.TYPE_INT_DEC:
                return "%d" % _data

        # raise exception here?
        return "<0x%X, type 0x%02X>" % (_data, _type)

    def complexToFloat(self, xcomplex):
        return (float)(xcomplex & 0xFFFFFF00) * tc.RADIX_MULTS[(xcomplex>>4) & 3];

    def getPackage(self, id):
        if id >> 24 == 1:
            return "android:"
        return ""

