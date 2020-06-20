# coding=utf-8
from __future__ import unicode_literals

import subprocess
import sys
import re

from io import open
from os import getenv
from urllib import urlopen
from json import loads
import datetime

# ==== CONSTANTS ====
Str = str or unicode

CHANGELOG_FILENAME = "CHANGELOG.md"
UNRELEASED_WORD = "Unreleased"

ADDED = "Added"
CHANGED = "Changed"
FIXED = "Fixed"
REMOVED = "Removed"

HOT_WORDS = {
    ADDED: [
        ADDED,
        "new",
        "feature",
        "добавлен",
        "добавлено",
        "добавлена",
        "фича",
    ],

    CHANGED: [
        CHANGED,
        "изменен",
        "изменён",
        "изменено",
        "изменена",
    ],

    FIXED: [
        FIXED,
        "fix",
        "пофикшен",
        "пофикшено",
        "пофикшена",
        "исправлен",
        "исправлено",
        "исправлена",
        "фикс",
    ],

    REMOVED: [
        REMOVED,
        "rm",
        "remove",
        "del",
        "delete",
        "deleted",
        "удален",
        "удалено",
        "удалена",
    ]
}
HW = {word.lower(): key for key, value in HOT_WORDS.items() for word in value}  # type: Dict[str, str]

UNRELEASED = {}  # type: Dict[str, List[str]]
TAGS = {}
CHANGELOG = {
    "unreleased": UNRELEASED,
    "tags_list": [],
    "tags": TAGS,
    "user": "",
    "repo": "",
}


# ==== UTILITY FUNCTIONS ====
def error(message, code=1):
    # type: (Str, int) -> None
    sys.stderr.write(message)
    return exit(code)


# ==== FORMAT STRING ====
class FORMAT(object):
    HEADER = '\n'.join(map(unicode.strip, """
    # Changelog
    All notable changes to this project will be documented in this file.
    
    The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
    and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
    """.strip().splitlines()))

    UNRELEASED_TAG = "## [%s]" % UNRELEASED_WORD
    TAG = "## [{tag}] - {date}"
    MODE = "### {mode}"
    CHANGELOG_LINE = " - {line}."

    UNRELEASED_LINK = "[%s]: https://github.com/{user}/{repo}/compare/{tags_list[0]}...HEAD" % UNRELEASED_WORD
    NO_TAG_LINK = "[%s]: https://github.com/{user}/{repo}" % UNRELEASED_WORD
    TAG_LINK = "[{tag_name}]: https://github.com/{user}/{repo}/compare/{before_tag}...{tag_name}"
    LAST_TAG_LINK = "[{tag_name}]: https://github.com/{user}/{repo}/releases/tag/{tag_name}"


# ==== REGULAR EXPRESSION CONSTANTS ====
class RE(object):
    # language=PythonRegExp
    REPO = re.compile(
        r"https://github\.com/(?P<user>[\w\-\d]+)/(?P<repo>[\w\-\d]+)"
    )
    # language=PythonRegExp
    DATE = re.compile(
        r"(?P<date>(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}))"
    )
    # language=PythonRegExp
    TAG = re.compile(
        r"v?(?P<ver>"
        r"(?P<maj>\d+)\.(?P<min>\d+)\.(?P<patch>\d+)"
        r")"
        r"(?:-(?P<pre>[0-9A-Za-z-]+))?"
        r"(?:\+(?P<build>[0-9A-Za-z-]))?"
    )
    # language=PythonRegExp
    TAG_LINE = re.compile(
        r"## \[(?P<tag>%s|%s)\](?: - %s)?" % (TAG.pattern, UNRELEASED_WORD, DATE.pattern)
    )
    # language=PythonRegExp
    # TAG_LINK = re.compile(
    #     r"\[(?P<tag>%s|%s)\]: %s" % (TAG.pattern, UNRELEASED_WORD, REPO.pattern)
    # )
    # language=PythonRegExp
    MODE = re.compile(
        r"### (?P<mode>%s)" % '|'.join(HOT_WORDS)
    )
    # language=PythonRegExp
    CHANGELOG_LINE = re.compile(
        r" - (?P<line>[\w\d].*)[.?!)]"
    )


# === PARSING CHANGELOG FILE ===
def parse_changelog(filename=CHANGELOG_FILENAME):
    repository = getenv("GITHUB_REPOSITORY")
    if repository is not None:
        CHANGELOG["user"] = repository.split('/', 1)[0]
        CHANGELOG["repo"] = repository.split('/', 1)[-1]
    else:
        with open(filename) as cl:
            search_repo = RE.REPO.search(cl.read())
            if search_repo is not None:
                CHANGELOG.update(search_repo.groupdict())
            else:
                error("User repository not found", 404)

    with open(filename) as cl:
        storage = None
        state = None
        for line in cl.readlines():
            m_tag = RE.TAG_LINE.match(line)
            m_mode = RE.MODE.match(line)
            m_changelog_line = RE.CHANGELOG_LINE.match(line)

            # Checking Tag
            if m_tag:
                tag = m_tag.groupdict()
                tag_name = tag["tag"]
                if tag_name == UNRELEASED_WORD:
                    storage = UNRELEASED
                    continue

                if tag_name in TAGS:
                    return error("Tag '%s' duplicated.")

                TAGS[tag_name] = {
                    "info": tag,
                    "storage": {}
                }
                CHANGELOG["tags_list"].append(tag_name)
                storage = TAGS[tag_name]["storage"]
                continue

            # Checking Mode
            if storage is not None and m_mode:
                state = m_mode.groupdict().get("mode")
                continue

            # Checking Changelog Line
            if storage is not None and state is not None and m_changelog_line:
                storage.setdefault(state, [])
                storage[state].append(m_changelog_line.groupdict().get("line"))
                continue

        # pprint(CHANGELOG)
        # with open("cl.json", 'w', encoding="utf-8") as f:
        #     f.write(unicode(dumps(CHANGELOG, ensure_ascii=False, indent=2)))


def check_commit(file_path):
    # type: (Str) -> int
    with open(file_path) as message:
        state = None  # like mode (ADDED, CHANGED, FIXED, REMOVED)
        for msg in message.readlines():
            msg = msg.strip()
            act = msg.lower().split(' ')[0].strip(':')
            if act in HW:
                state = HW[act]
                if not msg.endswith(':'):
                    UNRELEASED.setdefault(state, [])
                    line = msg[len(act):].strip().strip('.')
                    print "ADDED '%r'\tIN '%r'" % (line, state)
                    UNRELEASED[state].append(line)
                    state = None
                continue

            if state is not None:
                UNRELEASED.setdefault(state, [])
                s = UNRELEASED[state]
                if msg:
                    if msg.startswith('-') or msg.endswith('.'):
                        s.append(msg.strip('-').strip('.').strip())
                        if msg.endswith('.'):
                            s.append("")
                    elif not s:
                        s.append(msg)
                    else:
                        s[-1] = ' '.join((s[-1], msg)).strip()

                else:
                    state = None

    return save_changelog()


def generate_tag_version(tag):
    # type: (Str) -> Str
    if tag == UNRELEASED_WORD:
        result = FORMAT.UNRELEASED_TAG + '\n'
        store = CHANGELOG["unreleased"]

    else:
        tag_data = CHANGELOG["tags"][tag]
        result = FORMAT.TAG.format(**tag_data["info"]) + '\n'
        store = tag_data["storage"]

    for mode in sorted(HOT_WORDS):
        if mode in store:
            result += FORMAT.MODE.format(mode=mode) + "\n"
            for ln in store[mode]:
                result += FORMAT.CHANGELOG_LINE.format(line=ln.capitalize()) + '\n'
            result += '\n'

    return result.strip() + "\n\n"


def new_release(tag):
    # type: (Str) -> int
    tag_storage = UNRELEASED.copy()
    tag_str = FORMAT.TAG.format(tag=tag, date=datetime.date.today().isoformat())
    m_info = RE.TAG_LINE.match(tag_str)
    if m_info is None:
        error("'%s' is not a Tag." % tag)
    CHANGELOG["tags_list"].insert(0, tag)
    TAGS[tag] = {
        "info": m_info.groupdict(),
        "storage": tag_storage
    }
    release_body = '\n'.join(generate_tag_version(tag).splitlines()[1:])

    with open("release.txt", "w") as release_file:
        release_file.write(release_body)

    print "ADDED NEW RELEASE IN CHANGELOG: %s" % tag
    UNRELEASED.clear()
    return 0


def save_changelog():
    # type: () -> int
    # Clearing UNRELEASED
    for state, values in UNRELEASED.items():
        UNRELEASED[state] = [line.strip().capitalize() for line in filter(bool, values)]

    # print "==========="
    # pprint(CHANGELOG)
    # print "==========="

    # Generate a changelog unreleased string
    changelog_string = FORMAT.HEADER + "\n\n"

    for tag in [UNRELEASED_WORD] + CHANGELOG["tags_list"]:
        changelog_string += generate_tag_version(tag)

    # Generate links to tags
    if not CHANGELOG["tags_list"]:
        links_string = FORMAT.NO_TAG_LINK.format(**CHANGELOG)

    else:
        tags_list = CHANGELOG["tags_list"]
        links_string = '\n' + FORMAT.UNRELEASED_LINK.format(last_tag=tags_list[0], **CHANGELOG) + "\n\n"
        for index in range(len(tags_list) - 1):
            links_string += FORMAT.TAG_LINK.format(tag_name=tags_list[index],
                                                   before_tag=tags_list[index + 1], **CHANGELOG) + '\n'
        links_string += FORMAT.LAST_TAG_LINK.format(tag_name=tags_list[-1], **CHANGELOG)

    changelog_string += links_string
    # print "====================="

    # Save Changelog
    # print changelog_string
    with open(CHANGELOG_FILENAME, "w") as cl:
        cl.write(changelog_string)

    changed = "\tmodified:   " + CHANGELOG_FILENAME in subprocess.check_output("git status", shell=True)
    print "::set-env name=CHANGED_CHANGELOG::" + unicode(changed).lower()
    return 0


parse_changelog()
if __name__ == '__main__':
    argv = sys.argv[1:]
    DOMAIN = "https://api.github.com"

    if argv:
        release_tag = argv[0]
        new_release(release_tag)
        exit(save_changelog())

    sha = getenv("GITHUB_SHA")
    if sha:
        commit_data = loads(urlopen(str(
            DOMAIN + "/repos/%s/%s/commits/%s" % (CHANGELOG['user'], CHANGELOG['repo'], sha)
        )).read().decode("UTF-8"))

    else:
        commit_data = loads(urlopen(str(
            DOMAIN + "/repos/%s/%s/commits" % (CHANGELOG['user'], CHANGELOG['repo'])
        )).read().decode("UTF-8"))[0]

    with open(".temp.txt", "w") as temp:
        temp.write(commit_data['commit']['message'])

    check_commit(".temp.txt")
