from image_cache import ImageCache


def keys(cache):
    return [entry["key"] for entry in cache.to_list_front_to_back()]


def test_forward_and_backward_walk():
    cache = ImageCache(4)
    assert keys(cache) == ["lantern", "orchard", "summit", "harbor"]
    walker = cache.front_sentinel.next
    collected = []
    while walker is not cache.back_sentinel:
        collected.append(walker.key)
        walker = walker.next
    assert collected == ["lantern", "orchard", "summit", "harbor"]
    walker = cache.back_sentinel.previous
    reverse = []
    while walker is not cache.front_sentinel:
        reverse.append(walker.key)
        walker = walker.previous
    assert reverse == ["harbor", "summit", "orchard", "lantern"]


def test_access_promotes_to_front():
    cache = ImageCache(4)
    cache.get_image("harbor")
    assert keys(cache) == ["harbor", "lantern", "orchard", "summit"]
    assert cache.hits == 1


def test_miss_does_not_touch_order():
    cache = ImageCache(4)
    assert cache.get_image("ghost") is None
    assert cache.misses == 1
    assert keys(cache) == ["lantern", "orchard", "summit", "harbor"]


def test_eviction_drops_least_recently_used():
    cache = ImageCache(4)
    cache.get_image("harbor")
    cache.add_image("delta")
    assert keys(cache) == ["delta", "harbor", "lantern", "orchard"]
    assert cache.evictions == 1
    assert cache.ghost["key"] == "summit"
    assert cache.ghost["kind"] == "evicted"
    assert "summit" not in cache.entries


def test_existing_key_updates_without_eviction():
    cache = ImageCache(4)
    cache.add_image("harbor", "Harbor night")
    assert cache.size == 4
    assert cache.evictions == 0
    assert keys(cache) == ["harbor", "lantern", "orchard", "summit"]
    assert cache.entries["harbor"].title == "Harbor night"


def test_remove_middle_relinks_neighbours():
    cache = ImageCache(4)
    cache.remove_image("orchard")
    assert keys(cache) == ["lantern", "summit", "harbor"]
    assert cache.size == 3
    assert cache.entries["lantern"].next is cache.entries["summit"]
    assert cache.entries["summit"].previous is cache.entries["lantern"]
    assert cache.ghost["kind"] == "removed"


def test_cursor_walks_both_directions_and_blocks_at_edges():
    cache = ImageCache(4)
    cache.current_key = None
    cache.move_cursor("next")
    assert cache.current_key == "lantern"
    cache.move_cursor("next")
    assert cache.current_key == "orchard"
    cache.move_cursor("previous")
    assert cache.current_key == "lantern"
    cache.move_cursor("previous")
    assert cache.current_key == "lantern"
    assert cache.current_image()["previous_key"] == "HEAD"


def test_cursor_reports_both_neighbours():
    cache = ImageCache(4)
    cache.current_key = "summit"
    current = cache.current_image()
    assert current["previous_key"] == "orchard"
    assert current["next_key"] == "harbor"


def test_capacity_shrink_evicts_from_tail():
    cache = ImageCache(4)
    cache.set_capacity(2)
    assert keys(cache) == ["lantern", "orchard"]
    assert cache.size == 2
    assert cache.evictions == 2


def test_clear_resets_sentinels():
    cache = ImageCache(4)
    cache.clear_cache()
    assert cache.size == 0
    assert keys(cache) == []
    assert cache.front_sentinel.next is cache.back_sentinel
    assert cache.back_sentinel.previous is cache.front_sentinel
    assert cache.get_image("lantern") is None


def test_dirty_key_is_sanitized():
    cache = ImageCache(4)
    cache.add_image("../../etc", "Escape")
    assert "etc" in cache.entries
    assert cache.entries["etc"].image_url == "https://picsum.photos/seed/etc/360/260"
    cache.add_image("   ", "Blank")
    assert "" not in cache.entries


if __name__ == "__main__":
    for name, check in sorted(list(globals().items())):
        if name.startswith("test_"):
            check()
            print("ok", name)
