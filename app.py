from flask import Flask, redirect, render_template, request, url_for

from image_cache import ImageCache

app = Flask(__name__)
cache = ImageCache(4)


@app.route("/")
def index():
    payload = {
        "entries": cache.to_list_front_to_back(),
        "current": cache.current_image(),
        "stats": cache.statistics(),
        "events": cache.events,
        "highlight_key": cache.last_action_key,
        "ghost": cache.ghost,
    }
    cache.last_action_key = None
    cache.ghost = None
    return render_template("index.html", **payload)


@app.route("/add", methods=["POST"])
def add_image():
    cache.add_image(request.form.get("key", ""), request.form.get("title", ""))
    return redirect(url_for("index"))


@app.route("/access/<key>", methods=["POST"])
def access_image(key):
    cache.get_image(key)
    return redirect(url_for("index"))


@app.route("/remove/<key>", methods=["POST"])
def remove_image(key):
    cache.remove_image(key)
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear_cache():
    cache.clear_cache()
    return redirect(url_for("index"))


@app.route("/capacity", methods=["POST"])
def set_capacity():
    cache.set_capacity(request.form.get("capacity", 4))
    return redirect(url_for("index"))


@app.route("/cursor/<direction>", methods=["POST"])
def move_cursor(direction):
    cache.move_cursor(direction)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
