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


from . import bytecode
from . import typeconstants as tc
from .bytecode import SV
from .stringblock import StringBlock


class AXMLParser:

    def __init__(self, raw_buff):
        self.reset()

        self.buff = bytecode.BuffHandle(raw_buff)

        self.buff.read(4)
        self.buff.read(4)

        self.sb = StringBlock(self.buff)

        self.m_resourceIDs = []
        self.m_prefixuri = {}
        self.m_uriprefix = {}
        self.m_prefixuriL = []

    def reset(self):
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
        self.m_namespaceUri = -1
        self.m_attributes = []
        self.m_idAttribute = -1
        self.m_classAttribute = -1
        self.m_styleAttribute = -1

    def next(self):
        self.doNext()
        return self.m_event

    def doNext(self):
        if self.m_event == tc.END_DOCUMENT:
            return

        event = self.m_event

        self.reset()

        while 1:
            chunkType = -1

            # Fake END_DOCUMENT event.
            if event == tc.END_TAG:
                pass

            # START_DOCUMENT
            if event == tc.START_DOCUMENT:
                chunkType = tc.CHUNK_XML_START_TAG
            else:
                if self.buff.end() == True:
                    self.m_event = tc.END_DOCUMENT
                    break
                chunkType = SV('<L', self.buff.read(4)).get_value()

            if chunkType == tc.CHUNK_RESOURCEIDS:
                chunkSize = SV('<L', self.buff.read(4)).get_value()
                # FIXME
                if chunkSize < 8 or chunkSize%4 != 0:
                    raise("ooo")

                for i in range(0, int(chunkSize/4-2)):
                    self.m_resourceIDs.append(SV('<L', self.buff.read(4)))

                continue

            # FIXME
            if chunkType < tc.CHUNK_XML_FIRST or chunkType > tc.CHUNK_XML_LAST:
                raise("ooo")

            # Fake START_DOCUMENT event.
            if chunkType == tc.CHUNK_XML_START_TAG and event == -1:
                self.m_event = tc.START_DOCUMENT
                break

            self.buff.read(4) #/*chunkSize*/
            lineNumber = SV('<L', self.buff.read(4)).get_value()
            self.buff.read(4) #0xFFFFFFFF

            if chunkType == tc.CHUNK_XML_START_NAMESPACE or chunkType == tc.CHUNK_XML_END_NAMESPACE:
                if chunkType == tc.CHUNK_XML_START_NAMESPACE:
                    prefix = SV('<L', self.buff.read(4)).get_value()
                    uri = SV('<L', self.buff.read(4)).get_value()

                    self.m_prefixuri[ prefix ] = uri
                    self.m_uriprefix[ uri ] = prefix
                    self.m_prefixuriL.append((prefix, uri))
                else:
                    self.buff.read(4)
                    self.buff.read(4)
                    (prefix, uri) = self.m_prefixuriL.pop()
                    #del self.m_prefixuri[ prefix ]
                    #del self.m_uriprefix[ uri ]

                continue

            self.m_lineNumber = lineNumber

            if chunkType == tc.CHUNK_XML_START_TAG:
                self.m_namespaceUri = SV('<L', self.buff.read(4)).get_value()
                self.m_name = SV('<L', self.buff.read(4)).get_value()

                # FIXME
                self.buff.read(4) #flags

                attributeCount = SV('<L', self.buff.read(4)).get_value()
                self.m_idAttribute = (attributeCount>>16) - 1
                attributeCount = attributeCount & 0xFFFF
                self.m_classAttribute = SV('<L', self.buff.read(4)).get_value()
                self.m_styleAttribute = (self.m_classAttribute>>16) - 1

                self.m_classAttribute = (self.m_classAttribute & 0xFFFF) - 1

                for i in range(0, attributeCount * tc.ATTRIBUTE_LENGTH):
                    self.m_attributes.append(SV('<L', self.buff.read(4)).get_value())

                for i in range(tc.ATTRIBUTE_IX_VALUE_TYPE, len(self.m_attributes), tc.ATTRIBUTE_LENGTH):
                    self.m_attributes[i] = (self.m_attributes[i]>>24)

                self.m_event = tc.START_TAG
                break

            if chunkType == tc.CHUNK_XML_END_TAG:
                self.m_namespaceUri = SV('<L', self.buff.read(4)).get_value()
                self.m_name = SV('<L', self.buff.read(4)).get_value()
                self.m_event = tc.END_TAG
                break

            if chunkType == tc.CHUNK_XML_TEXT:
                self.m_name = SV('<L', self.buff.read(4)).get_value()

                # FIXME
                self.buff.read(4) #?
                self.buff.read(4) #?

                self.m_event = tc.TEXT
                break

    def getPrefixByUri(self, uri):
        try:
            return self.m_uriprefix[ uri ]
        except KeyError:
            return -1

    def getPrefix(self):
        try:
            return self.sb.getRaw(self.m_prefixuri[ self.m_namespaceUri ])
        except KeyError:
            return ""

    def getName(self):
        if self.m_name == -1 or (self.m_event != tc.START_TAG and self.m_event != tc.END_TAG):
            return ""

        return self.sb.getRaw(self.m_name)

    def getText(self):
        if self.m_name == -1 or self.m_event != tc.TEXT:
            return ""

        return self.sb.getRaw(self.m_name)

    def getNamespacePrefix(self, pos):
        prefix = self.m_prefixuriL[ pos ][0]
        return self.sb.getRaw(prefix)

    def getNamespaceUri(self, pos):
        uri = self.m_prefixuriL[ pos ][1]
        return self.sb.getRaw(uri)

    def getNamespaceCount(self, pos):
        pass

    def getAttributeOffset(self, index):
        # FIXME
        if self.m_event != tc.START_TAG:
            raise("Current event is not START_TAG.")

        offset = index * 5
        # FIXME
        if offset >= len(self.m_attributes):
            raise("Invalid attribute index")

        return offset

    def getAttributeCount(self):
        if self.m_event != tc.START_TAG:
            return -1

        return int(len(self.m_attributes) / tc.ATTRIBUTE_LENGTH)

    def getAttributePrefix(self, index):
        offset = self.getAttributeOffset(index)
        uri = self.m_attributes[offset + tc.ATTRIBUTE_IX_NAMESPACE_URI]

        prefix = self.getPrefixByUri(uri)
        if prefix == -1:
            return ""

        return self.sb.getRaw(prefix)

    def getAttributeName(self, index):
        offset = self.getAttributeOffset(index)
        name = self.m_attributes[offset + tc.ATTRIBUTE_IX_NAME]

        if name == -1:
            return ""

        return self.sb.getRaw(name)

    def getAttributeValueType(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + tc.ATTRIBUTE_IX_VALUE_TYPE]

    def getAttributeValueData(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + tc.ATTRIBUTE_IX_VALUE_DATA]

    def getAttributeValue(self, index):
        offset = self.getAttributeOffset(index)
        valueType = self.m_attributes[offset + tc.ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == tc.TYPE_STRING:
            valueString = self.m_attributes[offset + tc.ATTRIBUTE_IX_VALUE_STRING]
            return self.sb.getRaw(valueString)
        # WIP
        return ""
        #int valueData=m_attributes[offset+ATTRIBUTE_IX_VALUE_DATA];
        #return TypedValue.coerceToString(valueType,valueData);

