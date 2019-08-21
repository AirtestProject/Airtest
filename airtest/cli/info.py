# -*- coding: utf-8 -*-
__author__ = 'wjjn3033'

import os
import re
import sys
import six
import json
from io import open


def get_script_info(path):
    """extract info from script, like basename, __author__, __title__ and __desc__."""
    path = os.path.normpath(path)
    name = os.path.splitext(os.path.basename(path))[0]
    name_air = name + '.air'
    name_py = name + '.py'
    if path.endswith(".py"):
        parent_name = os.path.basename(os.path.dirname(path))
        pyfilepath = path
        if parent_name == name_air:
            script_name = name_air
            script_path = os.path.dirname(path)
        else:
            script_name = name_py
            script_path = path
    else:
        script_name = name_air
        script_path = path
        pyfilepath = os.path.join(path, name_py)

    if not os.path.exists(pyfilepath) and six.PY2:
        pyfilepath = pyfilepath.encode(sys.getfilesystemencoding())
    with open(pyfilepath, encoding="utf-8") as pyfile:
        pyfilecontent = pyfile.read()

    author, title, desc = get_author_title_desc(pyfilecontent)

    result_json = {"name": script_name, "path": script_path, "author": author, "title": title, "desc": desc}
    return json.dumps(result_json)


def get_author_title_desc(text):
    """Get author title desc."""
    regex1 = r'__(?P<attr>\w+)__\s*=\s*(?P<val>"[^"]+"|"""[^"]+""")'
    regex2 = r"__(?P<attr>\w+)__\s*=\s*(?P<val>'[^']+'|'''[^']+''')"
    data1 = re.findall(regex1, text)
    data2 = re.findall(regex2, text)
    data1.extend(data2)
    file_info = dict(data1)
    author = strip_str(file_info.get("author", ""))
    title = strip_str(file_info.get("title", ""))
    desc = strip_str(file_info.get("desc", ""))
    desc = process_desc(desc)
    return author, title, desc

def process_desc(desc):
    lines = desc.split('\n')
    lines = [line.strip() for line in lines]
    return '\n'.join(lines)

def strip_str(string):
    """Strip string."""
    return string.strip('"').strip("'").strip()
