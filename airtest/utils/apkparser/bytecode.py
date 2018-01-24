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

from struct import unpack, pack

global PRETTY_SHOW
PRETTY_SHOW = 0

# Print arg into a correct format
def _Print(name, arg):
    buff = name + " "

    if type(arg).__name__ == 'int':
        buff += "0x%x" % arg
    elif type(arg).__name__ == 'long':
        buff += "0x%x" % arg
    elif type(arg).__name__ == 'str':
        buff += "%s" % arg
    elif isinstance(arg, SV):
        buff += "0x%x" % arg.get_value()
    elif isinstance(arg, SVs):
        buff += arg.get_value().__str__()

    print(buff)

class SV:
    """SV is used to handle more easily a value"""
    def __init__(self, size, buff):
        self.__size = size
        self.__value = unpack(self.__size, buff)[0]

    def _get(self):
        return pack(self.__size, self.__value)

    def __str__(self):
        return "0x%x" % self.__value

    def __int__(self):
        return self.__value

    def get_value_buff(self):
        return self._get()

    def get_value(self):
        return self.__value

    def set_value(self, attr):
        self.__value = attr

class SVs:
    """SVs is used to handle more easily a structure of different values"""
    def __init__(self, size, ntuple, buff):
        self.__size = size

        self.__value = ntuple._make(unpack(self.__size, buff))

    def _get(self):
        l = []
        for i in self.__value._fields:
            l.append(getattr(self.__value, i))
        return pack(self.__size, *l)

    def _export(self):
        return [ x for x in self.__value._fields ]

    def get_value_buff(self):
        return self._get()

    def get_value(self):
        return self.__value

    def set_value(self, attr):
        self.__value = self.__value._replace(**attr)

    def __str__(self):
        return self.__value.__str__()

def object_to_str(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, int):
        return pack("<L", obj)
    elif obj == None:
        return ""
    else:
        #print type(obj), obj
        return obj.get_raw()

class MethodBC(object):
    def show(self, value):
        getattr(self, "show_" + value)()

class BuffHandle:
    def __init__(self, buff):
        self.__buff = buff
        self.__idx = 0

    def read_b(self, size):
        return self.__buff[ self.__idx: self.__idx + size ]

    def read(self, size):
        if isinstance(size, SV):
            size = size.value

        buff = self.__buff[ self.__idx: self.__idx + size ]
        self.__idx += size

        return buff

    def end(self):
        return self.__idx == len(self.__buff)

class Buff:
    def __init__(self, offset, buff):
        self.offset = offset
        self.buff = buff

        self.size = len(buff)

class _Bytecode(object):
    def __init__(self, buff):
        try:
            import psyco
            psyco.full()
        except ImportError:
            pass

        self.__buff = buff
        self.__idx = 0

    def read(self, size):
        if isinstance(size, SV):
            size = size.value

        buff = self.__buff[ self.__idx: self.__idx + size ]
        self.__idx += size

        return buff

    def readat(self, off):
        if isinstance(off, SV):
            off = off.value

        return self.__buff[ off: ]

    def read_b(self, size):
        return self.__buff[ self.__idx: self.__idx + size ]

    def set_idx(self, idx):
        if isinstance(idx, SV):
            self.__idx = idx.value
        else:
            self.__idx = idx

    def get_idx(self):
        return self.__idx

    def add_idx(self, idx):
        self.__idx += idx

    def register(self, type_register, fct):
        self.__registers[ type_register ].append(fct)

    def get_buff(self):
        return self.__buff

    def length_buff(self):
        return len(self.__buff)

    def save(self, filename):
        fd = open(filename, "w")
        buff = self._save()
        fd.write(buff)
        fd.close()

def FormatClassToJava(input):
    """
       Transofmr a typical xml format class into java format

       @param input: the input class name
    """
    return "L" + input.replace(".", "/") + ";"

def FormatClassToPython(input):
    i = input[:-1]
    i = i.replace("/", "_")
    i = i.replace("$", "_")

    return i

def FormatNameToPython(input):
    i = input.replace("<", "")
    i = i.replace(">", "")
    i = i.replace("$", "_")

    return i

def FormatDescriptorToPython(input):
    i = input.replace("/", "_")
    i = i.replace(";", "")
    i = i.replace("[", "")
    i = i.replace("(", "")
    i = i.replace(")", "")
    i = i.replace(" ", "")
    i = i.replace("$", "")

    return i

# class/method/field export
def ExportVMToPython(vm):
    """
        Export classes/methods/fields' names in the python namespace

        @param vm: a VM object (DalvikVMFormat, JVMFormat)
    """
    for _class in vm.get_classes():
        ### Class
        name = "CLASS_" + FormatClassToPython(_class.get_name())
        setattr(vm, name, _class)

        ### Methods
        m = {}
        for method in _class.get_methods():
            if method.get_name() not in m:
                m[ method.get_name() ] = []
            m[ method.get_name() ].append(method)

        for i in m:
            if len(m[i]) == 1:
                j = m[i][0]
                name = "METHOD_" + FormatNameToPython(j.get_name())
                setattr(_class, name, j)
            else:
                for j in m[i]:
                    name = "METHOD_" + FormatNameToPython(j.get_name()) + "_" + FormatDescriptorToPython(j.get_descriptor())
                    setattr(_class, name, j)

        ### Fields
        f = {}
        for field in _class.get_fields():
            if field.get_name() not in f:
                f[ field.get_name() ] = []
            f[ field.get_name() ].append(field)

        for i in f:
            if len(f[i]) == 1:
                j = f[i][0]
                name = "FIELD_" + FormatNameToPython(j.get_name())
                setattr(_class, name, j)
            else:
                for j in f[i]:
                    name = "FIELD_" + FormatNameToPython(j.get_name()) + "_" + FormatDescriptorToPython(j.get_descriptor())
                    setattr(_class, name, j)

class XREF:
    pass

def ExportXREFToPython(vm, gvm):
    for _class in vm.get_classes():
        for method in _class.get_methods():
            method.XREFfrom = XREF()
            method.XREFto = XREF()

            key = "%s %s %s" % (method.get_class_name(), method.get_name(), method.get_descriptor())

            if key in gvm.nodes:
                for i in gvm.G.predecessors(gvm.nodes[ key ].id):
                    xref = gvm.nodes_id[ i ]
                    xref_meth = vm.get_method_descriptor(xref.class_name, xref.method_name, xref.descriptor)
                    if xref_meth != None:
                        name = FormatClassToPython(xref_meth.get_class_name()) + "__" + FormatNameToPython(xref_meth.get_name()) + "__" + FormatDescriptorToPython(xref_meth.get_descriptor())
                        setattr(method.XREFfrom, name, xref_meth)

                for i in gvm.G.successors(gvm.nodes[ key ].id):
                    xref = gvm.nodes_id[ i ]
                    xref_meth = vm.get_method_descriptor(xref.class_name, xref.method_name, xref.descriptor)
                    if xref_meth != None:
                        name = FormatClassToPython(xref_meth.get_class_name()) + "__" + FormatNameToPython(xref_meth.get_name()) + "__" + FormatDescriptorToPython(xref_meth.get_descriptor())
                        setattr(method.XREFto, name, xref_meth)

def ExportDREFToPython(vm, vmx):
    for _class in vm.get_classes():
        for field in _class.get_fields():
            field.DREFr = XREF()
            field.DREFw = XREF()

            paths = vmx.tainted_variables.get_field(field.get_class_name(), field.get_name(), field.get_descriptor())
            if paths != None:
                for path in paths.get_paths():
                    if path.get_access_flag() == 'R':
                        method_class_name = path.get_method().get_class_name()
                        method_name = path.get_method().get_name()
                        method_descriptor = path.get_method().get_descriptor()

                        dref_meth = vm.get_method_descriptor(method_class_name, method_name, method_descriptor)
                        name = FormatClassToPython(dref_meth.get_class_name()) + "__" + FormatNameToPython(dref_meth.get_name()) + "__" + FormatDescriptorToPython(dref_meth.get_descriptor())
                        setattr(field.DREFr, name, dref_meth)
                    else:
                        method_class_name = path.get_method().get_class_name()
                        method_name = path.get_method().get_name()
                        method_descriptor = path.get_method().get_descriptor()

                        dref_meth = vm.get_method_descriptor(method_class_name, method_name, method_descriptor)
                        name = FormatClassToPython(dref_meth.get_class_name()) + "__" + FormatNameToPython(dref_meth.get_name()) + "__" + FormatDescriptorToPython(dref_meth.get_descriptor())
                        setattr(field.DREFw, name, dref_meth)

