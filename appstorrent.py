# /usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import argparse
import sys

from constants import *
from workflow import ICON_ERROR, ICON_WEB, ICON_INFO

__version__ = 'v0.1.0'


def _filter(data):
    return " ".join(filter(bool, (data.get(i, "") for i in (
            "title",
            "description",
            "id",
        ))))


@add_to_loading
def get_search_string(wf):
    # type: (Workflow) -> unicode
    d = (wf.cached_data("_search_dot", lambda: 1) or 1) % SEARCH_LENGTH
    wf.cache_data("_search_dot", d + 1)
    return ''.join(
        SEARCH_DOT_SELECTED if d == i else SEARCH_DOT
        for i in range(SEARCH_LENGTH)
    )


@add_to_loading
def get_loading_braille(wf):
    # type: (Workflow) -> unicode
    d = (wf.cached_data("_loading_braille", lambda: 1) or 1) % len(LOADING_BRAILLE)
    wf.cache_data("_loading_braille", d + 1)
    return LOADING_BRAILLE[d]


def main(wf):
    # type: (Workflow) -> None
    query = " ".join(wf.args)
    prefixes = []

    if PREFIX_SYMBOL_END in query:
        _pref, query = query.split(PREFIX_SYMBOL_END, 1)
        prefixes = list(filter(lambda x: x in _pref, PREFIXES))
        if not prefixes:
            query = _pref + PREFIX_SYMBOL_END + query

    if not prefixes and not query:
        wf.add_item(
            title="Добро пожаловать в AppStorrent!",
            subtitle="Выберите одну из категорий:"
        )
        wf.add_item(
            title="Программы",
            subtitle='Введите префикс `p:` для поиска',
            autocomplete="p:",
            icon=ICON_TECHNOLOGIST,
        )
        wf.add_item(
            title="Игры",
            subtitle='Введите префикс `g:` для поиска',
            autocomplete="g:",
            icon=ICON_VIDEO_GAME,
        )
        wf.add_item(
            title="Или используйте поиск самого сайта",
            subtitle='Введите префикс `s:` для поиска ⚠️ МОЖЕТ РАБОТАТЬ МЕДЛЕННО ⚠️',
            autocomplete="s:",
            icon=ICON_MAGNIFYING_GLASS_TILTED_LEFT,
        )
        wf.add_item(
            title="Настройки Workflow",
            subtitle="Введите `%s` для показа %d пуниктов настроек" % (
                wf.magic_prefix,
                len(wf.magic_arguments)
            ),
            icon=ICON_GEAR,
            autocomplete=wf.magic_prefix
        )
        if get_var_boolean("DEBUG"):
            wf.add_item(
                title="⚠️А может быть Вы хотите отчистить кеш♻️?)",
                subtitle='Особо страшного ничего не произойдёт, только придётся всё заново качать',
                autocomplete=wf.magic_prefix + "delcache"
            )

    if query.startswith(wf.magic_prefix):
        args = wf.filter(query.split(wf.magic_prefix, 1)[-1], sorted(wf.magic_arguments.items()),
                         lambda x: x[0])
        l = len(wf.magic_arguments)
        wf.add_item(
            title="Настройки Workflow",
            subtitle="%s настроек" % (
                l if l == len(args) else "%d из %d" % (
                    len(args), l
                )
            ),
            icon=ICON_GEAR,
            autocomplete=wf.magic_prefix
        )

        for key, func in args:
            wf.add_item(
                title=key,
                subtitle=wf.magic_prefix+key,
                autocomplete=wf.magic_prefix+key,
                icon=ICON_GEAR,
            )

    if "p" in prefixes:
        programs = wf.get_background_data(PROGRAMS, max_age=MAX_AGE, rerun_item=dict(
            title="Поиск по программам",
            autocomplete="p:",
            icon=ICON_TECHNOLOGIST,
        ))

        if programs is None:
            log.debug("Programs loadind...")

        elif "id" in prefixes:
            pr = list(filter(lambda x: x.get('id') == query, programs["data"]['items']))
            if not pr:
                wf.add_item(
                    title="Такой программы не существует!",
                    subtitle="Введите другой ID",
                    autocomplete="p:" + query,
                    icon=ICON_ERROR,
                )
            else:
                item = pr[0]  # type: dict
                icon = wf.cached_data(item['id'], None, 0)
                _id = item["id"]

                data = wf.get_background_data("info_" + _id, max_age=MAX_AGE, args=[_id], task="info", rerun_item=dict(
                    title='Получение данных о программе "%s"' % item['title'],
                    icon=icon,
                    autocomplete="pid:" + _id
                ))

                if data is not None:
                    wf.add_item(
                        title=data["name"],
                        subtitle=data["short_description"],
                        icon=icon,
                        type="file",
                        quicklookurl=item['href'],
                        copytext=item['href']
                    )
                    wf.add_item(
                        title="Последнее обновление: %s" % data['last_update'],
                        subtitle="Просмотров: %s" % data['views'],
                    )
                    wf.add_item(
                        title="Издатель / Автор",
                        subtitle=data["author"],
                        largetext=data["author"],
                        icon=ICON_BUSTS_IN_SILHOUETTE,
                    )

                    info = data["info"]  # type: dict
                    if info:
                        for k, v in info.items():
                            wf.add_item(
                                title=k,
                                subtitle=v,
                                largetext=v,
                                icon=ICON_INFO
                            )

                    wf.add_item(
                        title="Веб-сайт",
                        subtitle=data['website'],
                        arg=data["website"],
                        icon=ICON_WEB,
                        quicklookurl=data["website"],
                        valid=True
                    )
                    wf.add_item(
                        title="Описание (⌘+L для просмотра)",
                        subtitle=data["description"],
                        largetext=data["description"],
                        icon=ICON_PAGE_FACING_UP,
                    )
                    attachment = data['attachment']
                    if attachment['href']:
                        wf.add_item(
                            title=attachment['text'] or "Ссылка на скачивание",
                            subtitle=attachment['href'],
                            arg=attachment['href'],
                            icon=ICON_LINK,
                            valid=True
                        )
                    similar = data['similar']
                    if similar:
                        wf.add_item(
                            title="Похожие приложения:",
                            subtitle="Найдено %s штук" % len(similar),
                            icon=ICON_DESKTOP_COMPUTER
                        )
                        for i in similar:
                            s_icon = wf.cached_data(i['id'], None, 0)
                            wf.add_item(
                                title=i['title'],
                                subtitle="(↹ для доп. информации) %s  ●  %s" % (i["description"], i['version']),
                                autocomplete="pid:" + i['id'],
                                arg=i["href"],
                                icon=s_icon,
                                quicklookurl=s_icon,
                                copytext=i['href'],
                                valid=True,
                                largetext=i["title"],
                            )

        else:
            c = programs['data']['count']
            dat = wf.filter(query, programs['data']['items'], _filter)
            wf.add_item(
                title="Поиск по программам",
                subtitle='Найдено %s программ%s' % (
                    c if len(dat) == c else "%s из %s" % (len(dat), c),
                    'a' if c % 10 == 1 else (
                        'ы' if c % 10 in range(2, 5) else ''
                    )
                ),
                icon=ICON_TECHNOLOGIST,
                autocomplete="p:"
            )

            for item in dat:
                icon = wf.cached_data(item['id'], None, 0)
                i = wf.add_item(
                    title=item['title'],
                    subtitle="(↹ для доп. информации) %s  ●  %s" % (item["description"], item['version']),
                    autocomplete="pid:" + item['id'],
                    arg=item["href"],
                    icon=icon,
                    quicklookurl=icon,
                    copytext=item['href'],
                    valid=True,
                    largetext=item["title"],
                )
                i.add_modifier(
                    "cmd",
                    "Скопировать ссылку",
                    arg=item["href"],
                    valid=True
                )
                i.add_modifier(
                    "shift",
                    'Посмотреть "%s" в Alfred' % item['title'],
                    # valid=False
                )
                # wf.rerun = 2

    elif not wf._items:
        wf.add_item(
            title="Наверное, это ещё не работает...",
            subtitle="Напишите мне об этом!",
            arg="https://vk.com/im?sel=173996641"
        )

    if get_var_boolean("DEBUG"):
        wf.add_item(
            'Querry: "%s"' % query,
            'Prefixes: "%s" ' % '", "'.join(prefixes) if prefixes else 'No prefixes'
        )

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow(
        libraries=LIBRARIES,
        update_settings={
            'github_slug': 'jag-k/appstorrent-workflow',
            'version': __version__,
            # 'frequency': 7,
            'prereleases': '-beta' in __version__
        }
    )
    log = wf.logger
    log.setLevel("INFO")
    sys.exit(wf.run(main))
