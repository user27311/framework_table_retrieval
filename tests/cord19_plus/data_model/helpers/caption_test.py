import pytest
import json
from pathlib import Path
from papermage.magelib import Document
from data_model.helpers.caption import (
    text_matches_pattern,
    caption_in_layer,
    get_cleaned_captions,
    get_caption_for_box,
    get_fulltext_references,
    human_sort_key,
    get_table_name_from_caption,
    get_consecutive_ranges
)


@pytest.fixture()
def test_document():
    json_resp = Path(__file__).parent.parent.resolve() / "test_data" / "papermage_document.json"
    with open(json_resp, "r") as f:
        return Document.from_json(json.load(f))


@pytest.fixture()
def test_document_2():
    json_resp = Path(__file__).parent.parent.resolve() / "test_data" / "papermage_document_2.json"
    with open(json_resp, "r") as f:
        return Document.from_json(json.load(f))


@pytest.mark.parametrize(
    ("text", "layer"),
    [
        ("Fig. 1a", "figures"),
        ("fig. 123", "figures"),
        ("Figure 100", "figures"),
        ("figure test", "figures"),
        ("Table 10", "tables"),
        ("table 10", "tables"),
        ("tab.10", "tables"),
        ("Tab 1a-2b", "tables"),
    ],
)
def test_text_matches_pattern_success(text, layer):
    assert text_matches_pattern(text, layer)


@pytest.mark.parametrize("text", ["Test", "Bild 1", "Image", "foo"])
def test_text_matches_pattern_fail(text):
    assert not text_matches_pattern(text)


def test_caption_in_layer(test_document):
    caps = test_document.pages[3].captions
    res = []
    for cap in caps:
        res.append(caption_in_layer(page=test_document.pages[3], layer="figures", box=cap.boxes[0]))
    assert res == [False, False, False, True, True]


def test_get_cleaned_captions(test_document):
    caps = get_cleaned_captions(test_document)
    assert len(caps["tables"]) == 0 and caps["figures"] == [0, 1, 2, 7]


def test_get_cleaned_captions_2(test_document_2):
    caps = get_cleaned_captions(test_document_2)
    assert caps["tables"] == [4, 5, 9] and caps["figures"] == [0, 1, 2]


def test_get_caption_for_box(test_document):
    box = test_document.pages[4].figures[0].boxes[0]
    captions = test_document.pages[4].captions
    assert get_caption_for_box(box=box, captions=captions).startswith("Figure 4 Challenges reported by laboratories")


def test_get_caption_for_box_empty(test_document):
    box = test_document.pages[4].figures[0].boxes[0]
    captions = test_document.pages[4].captions
    assert get_caption_for_box(box=box, captions=captions, caption_ids=[2, 3]) == ""


@pytest.mark.parametrize(
    ("caption", "n", "expected_start"),
    [
        (
            "Table 1",
            3,
            [
                "papermage includes several ready - to - use Predictors that leverage",
                "Below , we showcase how a vision model and two text models",
                "Defining a Predictor . The pattern Lucy has followed is used in our many Predictor",
            ],
        ),
        (
            "Table 2",
            4,
            [
                "Recipes can also be flexibly modified to sup",
                "Though we found there are certain categories for which bounding box information",
                "Regardless , the way we represent structure in documents is highly versatile",
                "Here , we detail how we performed the evaluation reported in",
            ],
        ),
        (
            "Table 3",
            2,
            [
                "Though we found there are certain categories for which bounding box information",
                "Here , we detail how we performed the evaluation reported",
            ],
        ),
    ],
)
def test_get_fulltext_references(test_document_2, caption, n, expected_start):
    refs = get_fulltext_references(test_document_2, caption)
    assert len(refs) == n
    for i in range(len(refs)):
        assert refs[i].startswith(expected_start[i])


@pytest.mark.parametrize(
    ("values", "order"),
    [
        (["1", "11", "22", "3"], ["1", "3", "11", "22"]),
        (
            [
                "8arwlhf0_6_0",
                "8arwlhf0_12_0",
                "8arwlhf0_14_0",
                "8arwlhf0_15_0",
                "8arwlhf0_24_0",
                "8arwlhf0_25_0",
                "8arwlhf0_26_0",
                "8arwlhf0_27_0",
                "8arwlhf0_28_0",
                "8arwlhf0_29_0",
                "8arwlhf0_30_0",
                "8arwlhf0_31_0",
                "8arwlhf0_32_0",
            ],
            [
                "8arwlhf0_6_0",
                "8arwlhf0_12_0",
                "8arwlhf0_14_0",
                "8arwlhf0_15_0",
                "8arwlhf0_24_0",
                "8arwlhf0_25_0",
                "8arwlhf0_26_0",
                "8arwlhf0_27_0",
                "8arwlhf0_28_0",
                "8arwlhf0_29_0",
                "8arwlhf0_30_0",
                "8arwlhf0_31_0",
                "8arwlhf0_32_0",
            ],
        ),
        (
            [
                "41w1fe7k_0_0",
                "51w1fe7k_9_0",
                "51w1fe7k_10_0",
                "51w1fe7k_11_0",
                "51w1fe7k_11_1",
                "51w1fe7k_12_0",
                "51w1fe7k_12_1",
                "51w1fe7k_13_0",
                "51w1fe7k_14_0",
                "51w1fe7k_15_0",
                "51w1fe7k_16_0",
                "51w1fe7k_16_1",
                "51w1fe7k_16_2",
                "51w1fe7k_16_3",
                "51w1fe7k_16_4",
                "61w1fe7k_0_0",
            ],
            [
                "41w1fe7k_0_0",
                "51w1fe7k_9_0",
                "51w1fe7k_10_0",
                "51w1fe7k_11_0",
                "51w1fe7k_11_1",
                "51w1fe7k_12_0",
                "51w1fe7k_12_1",
                "51w1fe7k_13_0",
                "51w1fe7k_14_0",
                "51w1fe7k_15_0",
                "51w1fe7k_16_0",
                "51w1fe7k_16_1",
                "51w1fe7k_16_2",
                "51w1fe7k_16_3",
                "51w1fe7k_16_4",
                "61w1fe7k_0_0",
            ],
        ),
    ],
)
def test_human_sort_key(values, order):
    pass
    _sorted = sorted(values, key=human_sort_key)
    assert _sorted == order


@pytest.mark.parametrize(
    ("caption", "result"),
    [
        ("Tab. 1 sadadsd asdsa dsadas. asda sd.sad", "Tab. 1"),
        ("Table 1 klsd lalala asdsad salsa s. sa!()", "Table 1"),
        ("Table 1. klsd lalala asdsad salsa s. sa!()", "Table 1"),
        ("Table 1: klsd lalala asdsad salsa s. sa!()", "Table 1"),
        ("Table 11: klsd lalala asdsad salsa s. sa!()", "Table 11"),
        ("Table A-1 klsd lalala asdsad salsa s. sa!()", "Table A-1"),
        ("Table A-1: klsd lalala asdsad salsa s. sa!()", "Table A-1"),
        ("Tab. 1 klsd lalala asdsad salsa s. sa!()", "Tab. 1"),
        ("table 1 klsd lalala asdsad salsa s. sa!()", "table 1"),
        ("table 1: klsd lalala asdsad salsa s. sa!()", "table 1"),
        ("table 1_b klsd lalala asdsad salsa s. sa!()", "table 1_b"),
        ("table 1_b. klsd lalala asdsad salsa s. sa!()", "table 1_b"),
        ("table A-1 klsd lalala asdsad salsa s. sa!()", "table A-1"),
        ("table 1a klsd lalala asdsad salsa s. sa!()", "table 1a"),
        ("table 4.4. klsd lalala asdsad salsa s. sa!()", "table 4.4"),
        (
            "Table-1: Summary of in-vitro studies showing efficacy of hydroxychloroquine against "
            "SARS- CoV-2 infected Cell lines",
            "Table-1",
        ),
        (
            "Table 11: Summary of in-vitro studies showing efficacy of hydroxychloroquine against "
            "SARS- CoV-2 infected Cell lines",
            "Table 11",
        ),
    ],
)
def test_get_table_name_from_caption_success(caption, result):
    assert get_table_name_from_caption(caption) == result


@pytest.mark.parametrize(
    ("caption", "result"),
    [
        ("aaa table 1a klsd lalala asdsad salsa s. sa!()", None),
        ("table is klsd lalala asdsad salsa s. sa!()", None),
        ("tab1 is klsd lalala asdsad salsa s. sa!()", None),
        ("tab1.1 is klsd lalala asdsad salsa s. sa!()", None),
        ("table1 is klsd lalala asdsad salsa s. sa!()", None),
    ],
)
def test_get_table_name_from_caption_fail(caption, result):
    assert get_table_name_from_caption(caption) is None


@pytest.mark.parametrize(
    ("numbers", "result"),
    [
        ([1, 2, 3, 5, 6, 8, 12], [(1, 3), (5, 6), (8, 8), (12, 12)]),
        ([], []),
        ([1], [(1, 1)]),
        ([178, 179, 180, 530, 531, 532], [(178, 180), (530, 532)])
    ]
)
def test_get_consecutive_ranges(numbers, result):
    assert get_consecutive_ranges(numbers) == result
