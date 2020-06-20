from __future__ import unicode_literals

from io import open
import os
import subprocess
from zipfile import ZipFile
from plistlib import readPlist, writePlist
from appstorrent import __version__
from traceback import print_exc

DEFAULT_PLIST = "info.plist"


def update_plist(plist_file_or_path=None):
    # type: (str or file) -> int
    if plist_file_or_path is None:
        plist_file_or_path = DEFAULT_PLIST
    try:
        plist = readPlist(plist_file_or_path)
        plist["version"] = __version__.lstrip('v')
        if os.path.isfile("README.md"):
            with open("README.md", encoding="UTF-8") as readme_file:
                readme = readme_file.readlines()
                readme_lines = list(map(lambda x: x.lstrip("#").strip(), readme))
                name = readme_lines[0]
                if len(readme_lines) >= 2:
                    plist['description'] = readme_lines[1]

                plist['readme'] = '\n'.join(readme_lines)
                plist['name'] = name

        writePlist(plist, plist_file_or_path)
    except Exception as err:
        print_exc()
        print "%s: %s" % (type(err).__name__, err)
        return 1
    return 0


def build(filename, plist_file_or_path=None):
    # type: (str, str) -> str
    list_of_files = list(map(unicode, subprocess.check_output("git ls-files", shell=True).splitlines()))
    if os.path.isfile(".buildignore"):
        with open(".buildignore") as bi:
            for ignore in bi.readlines():
                ignore = ignore.strip()

                if ignore in list_of_files:
                    del list_of_files[list_of_files.index(ignore)]

    if plist_file_or_path is None or plist_file_or_path:
        update_plist(plist_file_or_path)

    # writing files to a zipfile
    with ZipFile(filename, 'w') as z:
        # writing each file one by one
        for f in list_of_files:
            z.write(f)

    print "::set-env name=TAG::" + __version__
    print "::set-env name=PRERELEASE::%s" % str("-" in __version__).lower()
    return filename


__all__ = ['build', 'update_plist']

if __name__ == '__main__':
    build(os.getenv("WORKFLOW_FILE", 'AppStorrent.alfredworkflow'))
