from papermage.magelib import Box


def contains(box1: Box, box2: Box) -> bool:
    return (
        box1.page == box2.page  # box on same page?
        and box1.l <= box2.l  # box2 is to the right of box1?
        and box1.l + box1.w >= box2.l + box2.w  # box2 right-top is left to the right-top of box1?
        and box1.t <= box2.t  # box2 is below box1
        and box1.t + box1.h >= box2.t + box2.h  # box2 left-bottom is above box1 left-bottom
    )


def intersects(box1: Box, box2: Box) -> bool:
    return not (
        box1.page != box2.page  # box is not on the same page
        or box1.l + box1.w <= box2.l  # box1 is completely to the left of box2
        or box2.l + box2.w <= box1.l  # box2 is completely to the left of box1
        or box1.t + box1.h <= box2.t  # box1 is completely above box2
        or box2.t + box2.h <= box1.t  # box2 is completely above box1
    )


def get_center(box: Box):
    return box.l + box.w / 2, box.t + box.h / 2
