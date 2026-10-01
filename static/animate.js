(function () {
  var targets = document.querySelectorAll("[data-animate]");
  targets.forEach(function (target) {
    var name = target.getAttribute("data-animate");
    target.classList.add(name);
    window.setTimeout(function () {
      target.classList.remove(name);
    }, 750);
  });
})();
