import pytest
from papermage.magelib import Box
from data_model.helpers.box import contains, intersects, get_center


@pytest.mark.parametrize(
    ("box1", "box2"),
    [
        (
            Box(l=0, t=0, w=0.5, h=0.5, page=0),
            Box(l=0.01, t=0.01, w=0.2, h=0.2, page=0),
        ),
        (Box(l=0, t=0, w=0.5, h=0.5, page=0), Box(l=0, t=0, w=0.5, h=0.5, page=0)),
    ],
)
def test_contains_success(box1: Box, box2: Box):
    assert contains(box1, box2)


@pytest.mark.parametrize(
    ("box1", "box2"),
    [
        (
            Box(l=0.01, t=0.01, w=0.2, h=0.2, page=0),
            Box(l=0, t=0, w=0.5, h=0.5, page=0),
        ),
        (Box(l=0, t=0, w=0.5, h=0.5, page=0), Box(l=0, t=0, w=0.51, h=0.5, page=0)),
        (
            Box(l=0, t=0, w=0.5, h=0.5, page=0),
            Box(l=0.01, t=0.01, w=0.2, h=0.2, page=2),
        ),
        (Box(l=0, t=0, w=0.5, h=0.5, page=1), Box(l=0, t=0, w=0.5, h=0.5, page=2)),
    ],
)
def test_contains_fail(box1: Box, box2: Box):
    assert not contains(box1, box2)


@pytest.mark.parametrize(
    ("box1", "box2"),
    [
        (Box(l=0, t=0, w=0.5, h=0.5, page=0), Box(l=0.4, t=0.4, w=0.2, h=0.2, page=0)),
        (
            Box(l=0, t=0, w=0.5, h=0.5, page=0),
            Box(l=0.499, t=0.4999, w=0.2, h=0.2, page=0),
        ),
    ],
)
def test_intersect_success(box1: Box, box2: Box):
    assert intersects(box1, box2)


@pytest.mark.parametrize(
    ("box1", "box2"),
    [
        (Box(l=0, t=0, w=0.1, h=0.1, page=0), Box(l=0.4, t=0.4, w=0.2, h=0.2, page=0)),
        (Box(l=0, t=0, w=0.5, h=0.5, page=0), Box(l=0.5, t=0.5, w=0.2, h=0.2, page=0)),
        (Box(l=0, t=0, w=0.5, h=0.5, page=0), Box(l=0.4, t=0.4, w=0.2, h=0.2, page=1)),
        (
            Box(l=0, t=0, w=0.5, h=0.5, page=2),
            Box(l=0.499, t=0.4999, w=0.2, h=0.2, page=4),
        ),
    ],
)
def test_intersect_fail(box1: Box, box2: Box):
    assert not intersects(box1, box2)


@pytest.mark.parametrize(
    ("box", "center"),
    [
        (Box(l=0, t=0, w=1, h=1, page=0), (0.5, 0.5)),
        (Box(l=10, t=10, w=50, h=100, page=0), (35, 60)),
    ],
)
def test_get_center(box, center):
    assert get_center(box) == center
