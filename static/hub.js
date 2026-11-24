(function () {
  function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
  fetch("/api/state").then(function (r) { return r.json(); }).then(function (d) {
    var keys = Object.keys(d.gifts).map(Number).sort(function (a, b) { return a - b; });
    document.getElementById("gifts").innerHTML = keys.map(function (k) {
      var g = d.gifts[k];
      return '<div class="gift"><div class="n">Gift #' + k + '</div><h3>' + esc(g.title) + '</h3><p>' + esc(g.message) + '</p></div>';
    }).join("") || "<p class='count'>Nothing unlocked yet. Go hunt!</p>";
  });
})();
