class CachedImage:
    def __init__(self, key, title=""):
        self.key = key
        self.title = title or key
        if key:
            self.image_url = "https://picsum.photos/seed/" + key + "/360/260"
            self.thumbnail_url = "https://picsum.photos/seed/" + key + "/160/120"
        else:
            self.image_url = ""
            self.thumbnail_url = ""
        self.previous = None
        self.next = None

    def is_detached(self):
        return self.previous is None and self.next is None
