# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import sys

from constants import *
from workflow.web import request, get


@Task(PROGRAMS)
def task_programs(wf):
    # type: (Workflow) -> None
    from appstorrent_api import get_data
    dat = wf.cached_data(PROGRAMS, lambda: get_data(
        PROGRAMS,
        sorting=wf.cached_data("sorting", None, 0)
    ), MAX_AGE)

    for i in dat['data']['items']:
        name, url = i["id"], i['img']
        wf.get_background_data(name, None, MAX_AGE*7, "download", [name, url])


@Task(GAMES)
def task_games(wf):
    # type: (Workflow) -> None
    from appstorrent_api import get_data
    dat = wf.cached_data(GAMES, lambda: get_data(
        GAMES,
        sorting=wf.cached_data("sorting", None, 0)
    ), MAX_AGE)

    for i in dat['data']['items']:
        name, url = i["id"], i['img']
        # cmd = ['/usr/bin/python', wf.workflowfile("update.py"), "download", name, url]
        # run_in_background("download_" + name, cmd)
        Task.run("download", name, url)


@Task("download")
def download_img(wf, name, url):
    # type: (Workflow, Str, Str) -> Str
    ext = url.rsplit('.', 1)[-1]
    img_name = os.path.abspath(join(ICON_DIR, "%s.%s" % (name, ext)))
    if not (os.path.exists(ICON_DIR) and os.path.isdir(ICON_DIR)):
        os.makedirs(ICON_DIR)
    d = request('get', url).raw
    with open(img_name, 'wb') as img:
        img.write(d.read())
    wf.cached_data(name, lambda: img_name, MAX_AGE * 7)
    return img_name


@Task("info")
def download_info(wf, _id):
    # type: (Workflow, Str) -> dict
    from appstorrent_api import join, BASE_URL, get_bs

    url = "https://www.appstorrent.ru/%s.html" % _id
    r = get(url).content
    bs = get_bs(r)

    info = {}

    bi = bs.find("div", {"class": "gameinfo"})
    # print(bi)
    for punkt in bi.findAll("div", {"class": "punkt"}):
        info[punkt.find("span").text] = punkt.find("p").text
    for punkt in bi.findAll("div", {"class": "punktscor"}):
        info[punkt.find("span").text] = punkt.find("div", {"class": "scora"}).text

    categories = {}
    for a in bs.find("div", {"class": "gameposterlink"}).findAll("a"):
        categories[a.get('href', '').strip("/").rsplit("/", 1)[-1]] = a.text

    # pprint(info)
    # pprint(categories)

    bd = bs.find("div", {"class": "gamefull"})
    bp = bs.find("ul", {"class": "pr-item"})

    similar = []
    for li in bp.findAll("li", {"class": "pr-item"}):
        a = li.find("a")
        similar.append({
            "id": a.get("href", '').strip('/').rsplit("/", 1)[-1].rsplit(".", 1)[0],
            "img": join(BASE_URL, a.find("img").get("src", "").strip("/")),
            "description": a.find("div", {"class": "pr-desc"}).text,
            "version": a.find("div", {"class": "pr-desc2"}).text,
            "title": a.find("div", {"class": "pr-title"}).text,
            "href": a.get("href", ''),
        })

    attachment_a = bs.find("a", {"class": "attachmentfile"})
    attachment = {
        "href": "",
        "text": ""
    } if attachment_a is None else {
        "href": attachment_a.get("href"),
        "text": attachment_a.text
    }

    res = {
        "website": bd.find("div", {"class": "gamefulltitle"}).find("a").get("href", ""),
        "views": int(bs.find("div", {"class": "viewsnews"}).text.replace(" ", "")),
        "short_description": bs.find("div", {"class": "gameposterfull"}).text,
        "description": bd.find("div", {"class": "gamefullglav"}).text,
        "last_update": bs.find("div", {"class": "calendarnews"}).text,
        "author": bs.find("div", {"class": "subtitgamefull"}).text,
        "name": bs.find("div", {"class": "titgamefull"}).text,
        "attachment": attachment,
        "similar": similar,
        "info": info,
    }
    # pprint(res)
    wf.cached_data("info_" + _id, lambda: res, MAX_AGE)
    return res


def main(wf):  # type: (Workflow) -> None or int
    query = wf.args
    Task.wf = wf

    try:
        wf.logger.warning("Start task: %s", "; ".join(query))
        Task.run(*query)
    finally:
        wf.send_feedback()


wf = Workflow(
    libraries=LIBRARIES
)
wf.run(main)
