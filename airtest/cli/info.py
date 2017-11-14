# -*- coding: utf-8 -*-
__author__ = 'wjjn3033'

import os
import re
import json
import traceback


def extract_param(param_name, pyfilecontent):
    # try to find tri ' " first, then single ' "
    reg_trian_author = "%s\s*=\s*(%s|%s).*?(%s|%s)" % (param_name, "'''", '"""', "'''", '"""')
    reg_single_author = "%s\s*=\s*(%s|%s).*?(%s|%s)" % (param_name, "'", '"', "'", '"')
    search_result = re.search(reg_trian_author, pyfilecontent, flags=re.S) or re.search(reg_single_author, pyfilecontent, flags=re.S)
    if search_result is not None:
        result_item = search_result.group()
        result_str = result_item.split("=")[-1].strip(" \'\"\r\n")
        return result_str
    else:
        return ""


def get_script_info(script_path, info_type='param'):
    """extract info from script, like __author__, __title__ and __desc__."""
    script_path, pyfilename = script_path, os.path.basename(script_path).replace(".owl", ".py")
    pyfilepath = os.path.join(script_path, pyfilename)

    try:
        with open(pyfilepath) as pyfile:
            pyfilecontent = pyfile.read()
    except Exception:
        traceback.print_exc()
        author, title, desc = "", "", ""
    else:
        if info_type == 'param':
            # extract params value from script:
            author = extract_param("__author__", pyfilecontent)
            title = extract_param("__title__", pyfilecontent)
            desc = extract_param("__desc__", pyfilecontent)

            result_json = {"author": author, "title": title, "desc": desc}
            return json.dumps(result_json)
        else:
            snapshot_result = extract_snapshot(pyfilecontent)
            return json.dumps(snapshot_result)


def extract_snapshot(pyfilecontent):
    snapshot_pattern = re.compile(r"snapshot\((msg=)?([\"\'](?P<msg>.*)[\"\'])?\)")
    ret = []
    for i in re.finditer(snapshot_pattern, pyfilecontent):
        msg = i.groupdict()
        ret.append(msg.get("msg") or "")
    return ret

