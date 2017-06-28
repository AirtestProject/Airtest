# coding=utf-8
__author__ = 'wjjn3033'

import os
import re
import json


def extarct_param(param_name, pyfilecontent):
    # try to find tri ' " first, then single ' "
    reg_trian_author = "%s\s*=\s*(%s|%s).*?(%s|%s)" % (param_name, "'''", '"""', "'''", '"""')
    reg_single_author = "%s\s*=\s*(%s|%s).*?(%s|%s)" % (param_name, "'", '"', "'", '"')
    search_result = re.search(reg_trian_author, pyfilecontent, flags=re.S) or re.search(reg_single_author, pyfilecontent, flags=re.S)
    if search_result is not None:
        result_item = search_result.group()
        result_str = result_item.split("=")[-1].strip(" \'\"\r\n")
        # 部分owl脚本提取后编码出错，此处做一下错误兼容
        try:
            result_str = result_str.encode("utf-8")
        except:
            pass

        return result_str
    else:
        return ""


def get_script_info(script_path):
    """extract info from script, like __author__, __title__ and __desc__."""
    script_path, pyfilename = script_path, os.path.basename(script_path).replace(".owl", ".py")
    pyfilepath = os.path.join(script_path, pyfilename)

    try:
        with open(pyfilepath) as pyfile:
            pyfilecontent = pyfile.read()
            # extract params value from script:
            author = extarct_param("__author__", pyfilecontent)
            title = extarct_param("__title__", pyfilecontent)
            desc = extarct_param("__desc__", pyfilecontent)
    except:
        author, title, desc = "", "", ""

    result_json = {"author": author, "title": title, "desc": desc}
    # return json.dumps(result_json, ensure_ascii=False)
    return json.dumps(result_json)
