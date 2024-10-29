import re
import math
from typing import Optional
from papermage.magelib import Document, Box, Entity, Layer
from cord19_plus.data_model.helpers.box import contains, get_center


def human_sort_key(filename):
    """
    Custom sorting function to extract numbers after the underscores

    :param filename:
    :return: tuple of numbers for custom sort with sorted()
    """
    return [int(text) if text.isdigit() else text for text in re.split(r"(\d+)", filename)]


def get_cleaned_captions(doc: Document) -> dict:

    return {
        "tables": [
            caption.id
            for page in doc.pages
            for caption in page.captions
            if text_matches_pattern(text=caption.text, layer="tables")
        ],
        "figures": [
            caption.id
            for page in doc.pages
            for caption in page.captions
            if text_matches_pattern(text=caption.text, layer="figures")
        ],
    }


def text_matches_pattern(text: str, layer: str = None) -> bool:
    if layer == "figures":
        return bool(re.search(r"^(fig.?)", text, flags=re.I))
    elif layer == "tables":
        return bool(re.search(r"^(tab.?)", text, flags=re.I))
    else:
        return bool(re.search(r"^(fig.?|tab.?)", text, flags=re.I))


def caption_in_layer(page: Entity, layer: str, box: Box) -> bool:
    layer = getattr(page, layer)
    for ent in layer:
        if contains(ent.boxes[0], box):
            return True
    return False


def get_caption_for_box(box: Box, captions: Layer, caption_ids: Optional[list] = None) -> str:
    ref_center = get_center(box)
    closest = float("inf")
    _text = ""
    for cap in captions:
        if caption_ids:
            if cap.id not in caption_ids:
                continue
        if box.page == cap.boxes[0].page:
            center = get_center(cap.boxes[0])
            dist = math.dist(ref_center, center)
            if dist < closest:
                closest = dist
                _text = cap.text
    return _text


def get_consecutive_ranges(numbers: list) -> list[tuple]:
    if not numbers:
        return []

    numbers = sorted(list(set(numbers)))  # sort the list, remove duplicates
    ranges = []
    start = numbers[0]
    end = numbers[0]

    for i in range(1, len(numbers)):
        if numbers[i] == end + 1:
            end = numbers[i]
        else:
            ranges.append((start, end))
            start = numbers[i]
            end = numbers[i]

    ranges.append((start, end))
    return ranges


def get_fulltext_references(doc: Document, caption: str) -> list:
    """
    if sentence contains caption: take sentence[i-1:i+2]

    :param doc: papermage Document
    :param caption: caption to look for in the full text
    :return: context surrounding caption
    """
    table = get_table_name_from_caption(caption)
    refs = []
    i_sent = []
 
    if table:
        for block in doc.blocks:
            # only consider boxes, that are not intersecting with captions
            if not block.intersect_by_box("captions"):
                if table in block.text:
                    refs.append(block.text[:500])
   
        # get sentence content if no boxes found
        if not refs:
            for i, sentence in enumerate(doc.sentences):

    
                if not (sentence.intersect_by_box("captions") or sentence.intersect_by_box("blocks")):
                    if table in sentence.text:

   
                        s = max(0, i - 1)
                        e = i + 1
                        # Replace table name at the beginning (dot can split into sentences)
                        caption = caption.replace(table, "", 1)
                        # make sure that captions are not considered
  
                        try:
                            if caption[2:35] not in doc.sentences[s].text:
                                i_sent.append(s)
                            if caption[2:35] not in doc.sentences[e].text:
                                i_sent.append(e)
                            if caption[2:35] not in doc.sentences[i].text:
                                i_sent.append(i)
                        except:
                            pass

 
            sent_ranges = get_consecutive_ranges(i_sent)
            for start, end in sent_ranges:
                # shorten every sentence to max of 120 chars
        
                ref = " ".join([sent.text[:120] for sent in doc.sentences[max(0, start): end + 1]])
                refs.append(ref[:360])
    return refs


def get_table_name_from_caption(caption: str) -> str:
    m = re.search(
        r"(^(tab[^ \t\r\f\n]+)([-\t \r\f])([a-z]?([_.-])?[0-9]+)([_.-])?[^\s:\-\.]?([a-z])?)", caption, flags=re.I
    )
    return m.group(0).rstrip(".:-") if m else None
