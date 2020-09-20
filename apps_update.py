from __future__ import unicode_literals, print_function
import sys
from os import walk, getenv
from os.path import abspath, join, split, splitext
from json import dumps

from xml.parsers.expat import ExpatError
# from plistlib import readPlist

# sys.path.append(abspath("./lib"))


APPLICATION_DIR = getenv("APPLICATION_DIR", "/Applications")
APPLICATION_EXT = ".app"
INFO_PLIST_FILENAME = "Info.plist"
PATH_TO_PLIST = join("Contents", INFO_PLIST_FILENAME)


def get_apps(start_dir):
    result = []
    try:
        _, paths, _ = next(walk(start_dir))
        for p in map(lambda x: join(start_dir, x), paths):
            if p.endswith(APPLICATION_EXT):
                result.append(p)
            else:
                result += get_apps(p)
    except StopIteration:
        return result
    return result


def get_versions():
    result = []
    for app_path in get_apps(APPLICATION_DIR):
        plist_path = join(app_path, PATH_TO_PLIST)
        data = get_info(plist_path, app_path)
        if data is not None:
            result.append(data)
    return result


def get_info(plist_path, app_path=None):
    from biplist import readPlist, InvalidPlistException

    try:
        plist = readPlist(plist_path)
        short_version = plist.get("CFBundleShortVersionString")
        version = plist.get("CFBundleVersion")
        name = plist.get("CFBundleName")
        display_name = plist.get("CFBundleDisplayName")

        if (display_name or name) and (short_version or version):
            return {
                "name": display_name or name,
                "version": short_version or version,

                "origin_name": name,
                "display_name": display_name,
                "origin_version": version,
                "short_version": short_version,

                "app_path": app_path,
                "plist_path": plist_path,

                "loaded": True,
            }
    except (ExpatError, InvalidPlistException):
        name = splitext(split(app_path)[-1])[0]
        return {
                "name": name,
                "version": None,

                "origin_name": name,
                "display_name": name,
                "origin_version": None,
                "short_version": None,

                "app_path": app_path,
                "plist_path": plist_path,

                "loaded": False,
            }


if __name__ == '__main__':
    res = get_versions()
    from io import open

    res = dumps(res, ensure_ascii=False, indent=2)
    with open("update.json", "w") as f:
            f.write(res)
    print(res)
