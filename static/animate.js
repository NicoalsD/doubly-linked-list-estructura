(function () {
  var STORAGE_KEY = "lru-chain-order";
  var FLIP_MS = 620;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var chain = document.getElementById("chain");
  var nodes = chain ? Array.prototype.slice.call(chain.querySelectorAll("[data-flip]")) : [];

  var keyOf = function (node) {
    return node.getAttribute("data-flip");
  };

  var readOrder = function () {
    try {
      return JSON.parse(window.sessionStorage.getItem(STORAGE_KEY)) || [];
    } catch (error) {
      return [];
    }
  };

  var writeOrder = function (order) {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(order));
    } catch (error) {
      return;
    }
  };

  var applyOrder = function (order) {
    var byKey = {};
    nodes.forEach(function (node) {
      byKey[keyOf(node)] = node;
    });
    order.forEach(function (key) {
      if (byKey[key]) {
        chain.appendChild(byKey[key]);
      }
    });
  };

  var measure = function () {
    var rects = {};
    nodes.forEach(function (node) {
      rects[keyOf(node)] = node.getBoundingClientRect();
    });
    return rects;
  };

  var playFlashes = function (delay) {
    window.setTimeout(function () {
      document.querySelectorAll("[data-animate]").forEach(function (target) {
        var name = target.getAttribute("data-animate");
        target.classList.add(name);
        window.setTimeout(function () {
          target.classList.remove(name);
        }, 950);
      });
    }, delay);
  };

  var entrance = function (stagger) {
    nodes.forEach(function (node, index) {
      if (stagger) {
        node.style.setProperty("--i", index);
      } else {
        node.style.setProperty("--i", 0);
      }
      node.classList.add("node-in");
    });
  };

  var flip = function (previous, current) {
    var rectsAfter = measure();
    applyOrder(previous);
    var rectsBefore = measure();
    applyOrder(current);

    nodes.forEach(function (node) {
      var key = keyOf(node);
      if (previous.indexOf(key) === -1) {
        node.style.setProperty("--i", 0);
        node.classList.add("node-in");
        return;
      }
      var dx = rectsBefore[key].left - rectsAfter[key].left;
      var dy = rectsBefore[key].top - rectsAfter[key].top;
      if (!dx && !dy) {
        return;
      }
      node.classList.add("flipping");
      node.style.transform = "translate3d(" + dx + "px," + dy + "px,0) rotateX(6deg)";
      window.requestAnimationFrame(function () {
        window.requestAnimationFrame(function () {
          node.classList.remove("flipping");
          node.classList.add("flip-run");
          node.style.transform = "translate3d(0,0,0) rotateX(6deg)";
        });
      });
      node.addEventListener("transitionend", function done() {
        node.removeEventListener("transitionend", done);
        node.classList.remove("flip-run");
        node.style.transform = "";
      });
    });
  };

  if (reduceMotion || !chain) {
    writeOrder(nodes.map(keyOf));
    return;
  }

  var current = nodes.map(keyOf);
  var previous = readOrder();
  writeOrder(current);

  if (!previous.length) {
    entrance(true);
    playFlashes(560);
  } else {
    flip(previous, current);
    playFlashes(FLIP_MS + 40);
  }
})();
