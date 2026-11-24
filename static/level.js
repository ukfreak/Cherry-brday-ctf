(function () {
  function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
  var n = window.LEVEL, msg = document.getElementById("smsg"), box = document.getElementById("sgift");
  var form = document.getElementById("sf"), input = document.getElementById("sflag");

  function showSolved(gift, next) {
    form.style.display = "none";
    msg.className = "ok";
    msg.textContent = "✅ Level " + n + " cleared!";
    box.innerHTML = '<div class="gift"><div class="n">Gift #' + n + '</div><h3>' + esc(gift.title) +
      '</h3><p>' + esc(gift.message) + '</p></div>' +
      (next ? '<a class="start" href="/level/' + next + '">Next level →</a>'
            : '<p>🎉 That was the last one!</p><a class="start" href="/love">💌 Open your last surprise →</a>');
  }

  fetch("/api/state").then(function (r) { return r.json(); }).then(function (d) {
    if (d.progress >= n) showSolved(d.gifts[String(n)], n < 29 ? n + 1 : null);
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    fetch("/api/solve", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level: n, flag: input.value })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok) { showSolved(d.gift, d.next); }
      else { msg.className = "err"; msg.textContent = "Not the right flag for this level. Keep looking!"; }
    });
  });
})();
