from django.conf import settings
from django.utils.safestring import mark_safe
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError
from .utils import truncate
from xml.etree.ElementTree import Element, ElementTree
import json
import logging


logger = logging.getLogger(__name__)


class ZoteroAPIException(Exception):
    pass


def format_zotero_as_html(zotero_item_id):
    try:
        return mark_safe(
            _zotero_api_request("format=bib", zotero_item_id)
            .read()
            .decode("utf-8")
            .replace('<?xml version="1.0"?>', "")
        )
    except ZoteroAPIException as e:
        msg = f"Loading Zotero item {zotero_item_id} failed"
        logger.warning(f"{msg}:")
        logger.warning(e)
        return mark_safe(msg)


def format_zotero_as_text(zotero_item_id):
    try:
        return _zotero_item_to_text(_load_zotero_item(zotero_item_id))
    except ZoteroAPIException as e:
        msg = f"Loading Zotero item {zotero_item_id} failed"
        logger.warning(f"{msg}:")
        logger.warning(e)
        return msg


def load_zotero_library():
    try:
        return _load_zotero_atom("content=json&order=title&limit=99")
    except ZoteroAPIException as e:
        logger.warning("Loading Zotero library failed:")
        logger.warning(e)
        return []


def _zotero_api_request(query: str, zotero_item_id=None):
    path = "" if zotero_item_id is None else f"/{zotero_item_id}"
    url = (
        f"https://api.zotero.org/groups/{settings.ZOTERO_GROUP_ID}/items{path}?{query}"
    )
    try:
        return urlopen(url)
    except (URLError, HTTPError) as e:
        raise ZoteroAPIException() from e


def _zotero_item_to_text(item):
    def name(creator):
        if "name" in creator:
            return creator["name"]
        return "%s %s" % (
            creator.get("firstName", "[missing first name]"),
            creator.get("lastName", "[missing last name]"),
        )

    return "%s (%s)" % (
        item.get("title", "[missing title]"),
        ", ".join([name(c) for c in item.get("creators", [])]),
    )


def _get_element_text(tree_or_element: ElementTree | Element, element_name: str) -> str:
    e = tree_or_element.find(element_name)
    if e is None or e.text is None:
        raise ZoteroAPIException(f"missing element: {element_name}")
    return e.text


def _load_zotero_item(zotero_item_id):
    tree = ElementTree()
    tree.parse(_zotero_api_request("content=json", zotero_item_id))
    return json.loads(_get_element_text(tree, "{http://www.w3.org/2005/Atom}content"))


def _load_zotero_atom(query: str):
    tree = ElementTree()
    library = []
    tree.parse(_zotero_api_request(query))
    for entry in tree.findall("{http://www.w3.org/2005/Atom}entry"):
        item_type = _get_element_text(entry, "{http://zotero.org/ns/api}itemType")
        if item_type == "attachment":
            continue
        key = _get_element_text(entry, "{http://zotero.org/ns/api}key")
        content = _get_element_text(entry, "{http://www.w3.org/2005/Atom}content")
        try:
            library.append((key, truncate(_zotero_item_to_text(json.loads(content)))))
        except KeyError:
            continue
    for link in tree.findall("{http://www.w3.org/2005/Atom}link"):
        if link.attrib.get("rel", None) == "next":
            library.extend(_load_zotero_atom(urlparse(link.attrib["href"]).query))
            break
    return library
