# /usr/bin/python3
import sys
import os
from os.path import join, abspath
from requests import get

from bs4 import BeautifulSoup, Tag

URL = "https://emojipedia.org/search/?q="
ICONS_DIR = abspath(join(os.curdir, "icons"))

icons = sys.argv[1:] if sys.argv[1:] else [input("Enter Emoji: ")]

for icon in icons:
    page = get(URL + icon)
    bs = BeautifulSoup(page.text, "lxml")
    icon = bs.find("div", {"class": "vendor-image"})  # type: Tag
    if icon:
        print(bs.find("title").text)
        src = icon.find("img").get("src", "")
        if not os.path.exists(ICONS_DIR):
            os.makedirs(ICONS_DIR)

        ext = src.rsplit('.', 1)[-1]
        name = page.url.strip('/').rsplit('/', 1)[-1]
        p = join(ICONS_DIR, name + '.' + ext)

        icon_data = get(src)
        with open(p, "wb") as i:
            i.write(icon_data.content)
        print("Save in path:", p)

    else:
        print("Input `%s` is not Emoji" % icon, file=sys.stderr)
