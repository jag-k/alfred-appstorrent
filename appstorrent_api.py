from __future__ import print_function, unicode_literals

from collections import Callable
from json import dumps
from os.path import join
from urllib2 import build_opener, HTTPError

from bs4 import BeautifulSoup, Tag, FeatureNotFound

CATEGORY = ''
BASE_URL = "https://www.appstorrent.ru"

DEFAULT_SORT = ""


def pprint(item):
    try:
        print(dumps(item, ensure_ascii=False, indent=2))
    except TypeError:
        print(item)


def get_bs(html):
    # type: (Str) -> BeautifulSoup
    try:
        return BeautifulSoup(html, "html.parser")
    except FeatureNotFound:
        return BeautifulSoup(html)


def get_data_by_url(url, cookie=None):
    # type: (Str, dict) -> Str
    if not cookie:
        cookie = {}
    opener = build_opener()
    opener.addheaders.append(('Cookie', "; ".join('%s=%s' % (k, v) for k, v in cookie.items())))
    # print(url, opener.addheaders)
    try:
        return opener.open(url)
    except HTTPError:
        return ''


def get_navigation(bs=None):
    # type: (BeautifulSoup) -> Tuple[list, dict]
    if type(bs) is not BeautifulSoup:
        bs = get_bs(get_data_by_url(BASE_URL))

    navigations = []
    navigations_dict = {}
    for a in bs.find("div", {"class": "list-group2"}).findAll('a'):  # type: Tag
        name, count = list(a.stripped_strings)
        href = a.get("href", '/').lstrip('/')
        if href in FILTER:
            navigations.append({
                "name": name,
                "href": href,
                "count": int(count)
            })
            navigations_dict[href] = int(count)
    return navigations, navigations_dict


def get_data(_type=None, category=None, sorting=None, print_percents=False):
    # type: (Str, Str, Str or int, bool) -> dict
    if _type not in FILTER:
        return {}

    bs = get_bs(get_data_by_url(join(BASE_URL, _type)))

    categories = {
        s.get("value").strip('/').rsplit('/', 1)[-1]: s.text

        for s in bs.find(
            "select",
            {"id": "dle_sort", "onchange": "top.location=this.value"}
        ).findAll(
            "option",
            {"hidden": False}
        )
    }

    if category not in categories:
        category = ''

    sort = {
        o.get("value"): {
            "key": o.get("data-value"),
            "value": o.get("value"),
            "name": o.text,
        }
        for o in bs.find("select", {"id": "dle_sort"}).findAll("option")
    }
    if not (sorting in sort or str(sorting) in sort):
        sorting = DEFAULT_SORT

    data = FILTER[_type](category=category, percents=print_percents, href=_type, sorting=sorting)  # type: list

    return {
        "categories": categories,
        "category": category,
        "find_type": _type,
        "sorting": sorting,
        "sort": sort,
        "data": {
            "count": len(data),
            "items": data
        }
    }


def constructor(name, attrs, selector_func, _href=''):
    # type: (Str, dict, Callable, Str) -> Callable
    def dec(category=CATEGORY, href=_href, percents=False, **kwargs):
        res = []
        url = join(BASE_URL, href, category, "page/%s")
        page_number = 1

        data = get_data_by_url(url % page_number, {
            "remember_select": kwargs.get("sorting", DEFAULT_SORT)
        })

        bs = get_bs(data)

        try:
            total_count = NAVIGATIONS_DICT[href]
        except NameError:
            global NAVIGATIONS, NAVIGATIONS_DICT
            NAVIGATIONS, NAVIGATIONS_DICT = get_navigation(bs)
            total_count = NAVIGATIONS_DICT[href]

        while True:
            have_elements = False
            for tag in bs.findAll(name, attrs):  # type: Tag
                have_elements = True
                res.append(selector_func(tag))
                if percents:
                    print("\r%s%% (%s / %s)" % (
                        int((float(len(res)) / float(total_count)) * 100),
                        len(res),
                        total_count
                    ),
                          end='')

            if not have_elements:
                if percents:
                    print('\r', end="")
                return res

            page_number += 1
            data = get_data_by_url(url % page_number, {
                "remember_select": kwargs.get("sorting", DEFAULT_SORT)
            })

            bs = get_bs(data)

    return dec


FILTER = {
    "programs": constructor(
        'a',
        {"class": "pr-itema"},
        lambda a: {
            "href": a.get("href", ""),
            "id": a.get("href", "").rsplit('/', 1)[-1].rsplit('.', 1)[0],
            "img": join(BASE_URL, a.find("img", {"class": "program-icon"}).get("src").strip('/')),
            "title": a.find("div", {"class": "pr-title"}).text,
            "description": a.find("div", {"class": "pr-desc"}).text,
            "version": a.find("div", {"class": "pr-desc2"}).text,
        },
        "programs"
    ),
    "games": constructor(
        "li",
        {"class": "games-item"},
        lambda li: {
            "href": li.find('a').get("href", ""),
            "id": li.find('a').get("href", "").rsplit('/', 1)[-1].rsplit('.', 1)[0],
            "img": join(BASE_URL, li.find("img", {"class": "games-icon"}).get("src").strip('/')),
            "title": li.find("div", {"class": "games-title"}).text,
            "description": ' '.join(filter(bool, li.find("div", {"class": "games-desc"}).text.split())),
            "category": ''.join(filter(bool, li.find("div", {"class": "games-desc"}).text.split())).split('/')[1:]
        },
        "games"
    )
}

if __name__ == '__main__':
    NAVIGATIONS, NAVIGATIONS_DICT = get_navigation()
    print(dumps(
        get_data("games"),
        ensure_ascii=False,
        indent=2
    ))
