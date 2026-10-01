from cached_image import CachedImage

DEMO_KEYS = ["harbor", "summit", "orchard", "lantern"]


class ImageCache:
    def __init__(self, capacity=4):
        self.capacity = capacity
        self.size = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.entries = {}
        self.events = []
        self.current_key = None
        self.last_action_key = None
        self.ghost = None
        self.front_sentinel = CachedImage("")
        self.back_sentinel = CachedImage("")
        self.front_sentinel.next = self.back_sentinel
        self.back_sentinel.previous = self.front_sentinel
        self.load_demo_images()

    def load_demo_images(self):
        for key in DEMO_KEYS:
            self.add_image(key, key.capitalize())

    def _record(self, message):
        self.events = [message] + self.events[:6]

    def _detach(self, entry):
        entry.previous.next = entry.next
        entry.next.previous = entry.previous
        entry.previous = None
        entry.next = None

    def _attach_front(self, entry):
        entry.next = self.front_sentinel.next
        entry.previous = self.front_sentinel
        self.front_sentinel.next.previous = entry
        self.front_sentinel.next = entry

    def _drop(self, entry, kind):
        self._detach(entry)
        del self.entries[entry.key]
        self.size = self.size - 1
        self.ghost = {
            "key": entry.key,
            "title": entry.title,
            "thumbnail_url": entry.thumbnail_url,
            "kind": kind,
        }
        if self.current_key == entry.key:
            self.current_key = None

    def _evict_oldest(self):
        oldest = self.back_sentinel.previous
        if oldest is self.front_sentinel:
            return None
        self._drop(oldest, "evicted")
        self.evictions = self.evictions + 1
        self._record("EVICT " + oldest.key + " LRU unlinked from TAIL")
        return oldest

    @staticmethod
    def _clean_key(key):
        return "".join(c for c in (key or "").lower() if c.isalnum() or c == "-")[:24]

    def get_image(self, key):
        entry = self.entries.get(key)
        if entry is None:
            self.misses = self.misses + 1
            self.last_action_key = key
            self._record("GET " + key + " MISS not cached")
            return None
        self.hits = self.hits + 1
        self._detach(entry)
        self._attach_front(entry)
        self.current_key = key
        self.last_action_key = key
        self._record("GET " + key + " HIT promoted to MRU")
        return entry

    def add_image(self, raw_key, title=""):
        key = self._clean_key(raw_key)
        if not key:
            self._record("ADD rejected key must be alphanumeric")
            return None
        existing = self.entries.get(key)
        if existing is not None:
            if title:
                existing.title = title
            self._detach(existing)
            self._attach_front(existing)
            self.current_key = key
            self.last_action_key = key
            self._record("ADD " + key + " already cached value updated and promoted")
            return existing
        if self.size >= self.capacity:
            self._evict_oldest()
        entry = CachedImage(key, title)
        self.entries[key] = entry
        self._attach_front(entry)
        self.size = self.size + 1
        self.current_key = key
        self.last_action_key = key
        self._record("ADD " + key + " inserted at MRU size " + str(self.size))
        return entry

    def remove_image(self, key):
        entry = self.entries.get(key)
        if entry is None:
            self.misses = self.misses + 1
            self._record("REMOVE " + key + " not cached")
            return False
        follower = entry.next
        self._drop(entry, "removed")
        if self.current_key is None and follower is not self.back_sentinel:
            self.current_key = follower.key
        self.last_action_key = None
        self._record("REMOVE " + key + " neighbours relinked size " + str(self.size))
        return True

    def clear_cache(self):
        self.entries = {}
        self.size = 0
        self.current_key = None
        self.last_action_key = None
        self.ghost = None
        self.front_sentinel.next = self.back_sentinel
        self.back_sentinel.previous = self.front_sentinel
        self._record("CLEAR every link reset to sentinels")

    def set_capacity(self, raw_capacity):
        try:
            value = int(raw_capacity)
        except (TypeError, ValueError):
            value = self.capacity
        self.capacity = max(1, min(10, value))
        while self.size > self.capacity:
            self._evict_oldest()
        self._record("CAPACITY now " + str(self.capacity))

    def move_cursor(self, direction):
        if self.size == 0:
            self.current_key = None
            self._record("CURSOR blocked cache empty")
            return None
        entry = self.entries.get(self.current_key)
        if entry is None:
            self.current_key = self.front_sentinel.next.key
            self._record("CURSOR reset to MRU " + self.current_key)
            return self.current_image()
        if direction == "next":
            target = entry.next
            if target is self.back_sentinel:
                self._record("CURSOR next blocked at TAIL")
                return self.current_image()
        else:
            target = entry.previous
            if target is self.front_sentinel:
                self._record("CURSOR previous blocked at HEAD")
                return self.current_image()
        self.current_key = target.key
        self._record("CURSOR " + direction + " from " + entry.key + " to " + target.key)
        return self.current_image()

    def current_image(self):
        entry = self.entries.get(self.current_key)
        if entry is None:
            return None
        return {
            "key": entry.key,
            "title": entry.title,
            "image_url": entry.image_url,
            "previous_key": "HEAD" if entry.previous is self.front_sentinel else entry.previous.key,
            "next_key": "TAIL" if entry.next is self.back_sentinel else entry.next.key,
        }

    def to_list_front_to_back(self):
        result = []
        walker = self.front_sentinel.next
        while walker is not self.back_sentinel:
            result.append({
                "key": walker.key,
                "title": walker.title,
                "thumbnail_url": walker.thumbnail_url,
            })
            walker = walker.next
        return result

    def statistics(self):
        return {
            "size": self.size,
            "capacity": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
        }
