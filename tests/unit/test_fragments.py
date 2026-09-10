from snackapp.app import intersecting_fragments


def test_intersection_selects_readers_of_written_collection():
    reads = {"board": {"deals"}, "stats": {"deals"}, "notes": {"notes"}}
    wrote = {"deals"}
    assert intersecting_fragments(reads, wrote, {"deals", "notes"}) == ["board", "stats"]


def test_empty_fragment_inherits_page_reads():
    reads = {"shell": set()}
    wrote = {"deals"}
    assert intersecting_fragments(reads, wrote, {"deals"}) == ["shell"]
