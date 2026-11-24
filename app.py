import base64, hashlib, hmac, json, os, posixpath, secrets, sqlite3
from datetime import timedelta
from flask import (Flask, request, render_template_string, make_response,
                   jsonify, Response, redirect, session, send_from_directory)

app = Flask(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))


def _secret_key():
    env = os.environ.get("SECRET_KEY")
    if env:
        return env
    path = os.path.join(HERE, ".secret_key")
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        key = secrets.token_hex(32)
        try:
            with open(path, "w") as f:
                f.write(key)
        except OSError:
            pass
        return key


app.secret_key = _secret_key()
app.permanent_session_lifetime = timedelta(days=365)

TAGS = {1: "TW", 2: "BM", 3: "SC", 4: "KJ", 5: "FR", 6: "HW", 7: "DPB", 8: "HKC", 9: "HJ",
        10: "CP", 11: "JP", 12: "NP", 13: "SMC", 14: "EC", 15: "SC", 16: "GKC", 17: "RSS",
        18: "HG", 19: "CK", 20: "KK", 21: "BS", 22: "HOC", 23: "MC", 24: "C3", 25: "FC",
        26: "MC", 27: "LTRMOY", 28: "WV", 29: "VYS"}


def flag(n):
    return "CherryBrdayGift{%02d_%s}" % (n, TAGS[n])


def load_json(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


GIFTS = load_json("gifts.json")
QUIZ = load_json("quiz.json")

LEVEL_TITLES = {
    1: "Warm-up", 2: "Look closer", 3: "Not for bots", 4: "Knock knock", 5: "Hex marks the spot",
    6: "Rotate me", 7: "Cookie monster", 8: "Console star", 9: "Headers up", 10: "Trust issues",
    11: "How well do you know me?", 12: "Client-side security", 13: "Oops, a leftover", 14: "Someone else's gift",
    15: "Debug mode", 16: "The boss's office", 17: "Invisible ink", 18: "Dots and dashes", 19: "Ones and zeros",
    20: "Style check", 21: "Pocket money", 22: "Locked button", 23: "A map for crawlers", 24: "For humans",
    25: "Say hello", 26: "Out of bounds", 27: "Backwards", 28: "Cherry clicker", 29: "The final gift",
}

HINTS = {
    1: "That blob of text looks like it ends with '=' ... what encoding is that?",
    2: "Browsers show you the page. Developers see more. Try View Source (Ctrl+U).",
    3: "Websites politely tell crawlers where NOT to go. There is a standard file for that.",
    4: "Classic login form. What if the password field isn't just a password? Try  ' OR '1'='1",
    5: "Those characters only go up to F. Convert hex to text.",
    6: "Caesar's favourite shift, in its most famous form (13).",
    7: "The server decides who you are using something stored in your browser. Open DevTools > Application > Cookies.",
    8: "Open DevTools > Console. Some things are stored in variables...",
    9: "Not everything is in the page. Check the Network tab > Response Headers.",
    10: "The form has a field you can't see. DevTools lets you edit it before you submit.",
    11: "Answer honestly. (Case does not matter.)",
    12: "The password check runs in YOUR browser. That means you can read it.",
    13: "Developers sometimes leave backup files. Try config.php.bak",
    14: "You are looking at gift id=5. Whose gift is id=1?",
    15: "Developers love debug flags. Try adding ?debug=true to the URL.",
    16: "Where would you expect to find an admin panel? Try adding /admin to the site address.",
    17: "Some text is there but you can't see it. Select everything (Ctrl+A).",
    18: "Use the chart on the page to decode each letter. The answer is the middle of the flag: CherryBrdayGift{ ANSWER }",
    19: "8 bits per character. Paste it into any 'binary to text' website. The answer goes inside CherryBrdayGift{ }",
    20: "The page is styled by a CSS file. View Source, find the .css link, open it and read the comments.",
    21: "Websites can keep things in your browser. DevTools (F12) > Application > Local Storage.",
    22: "The button is disabled. In DevTools (F12) > Elements, delete the word 'disabled' from the button, then click it.",
    23: "There is another standard file crawlers read, listing pages. Starts with 's'. Try /sitemap.xml",
    24: "Robots have robots.txt. Humans have a file too. Try /humans.txt",
    25: "The page prints your name without cleaning it. Try this as your name:  <img src=x onerror=alert(1)>",
    26: "Go up one folder with ../ . Try changing the URL to end with ?name=../secret/flag.txt",
    27: "Just read it from the end to the start. Paste it into any 'reverse text' website.",
    28: "Click the cherry. Keep clicking. (Or be sneaky and read the page's source.)",
    29: "Three pieces, three tricks you already know: View Source, the Console (F12), and the Network tab > Response Headers.",
}

LAYOUT = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} - Cherry's Birthday CTF</title>
<link rel="stylesheet" href="/static/style.css">{{ head|safe }}</head>
<body><header><a href="/" class="logo">🍒 Cherry's Birthday CTF</a></header>
<main><div class="card">
{% if n %}<p class="lvl">Level {{ n }} / 29</p>{% endif %}
<h1>{{ title }}</h1>
{{ body|safe }}
{% if n %}<div class="submit"><h3>🚩 Got the flag?</h3>
<form id="sf"><input id="sflag" placeholder="CherryBrdayGift{...}" autocomplete="off"><button>Submit flag</button></form>
<p id="smsg"></p><div id="sgift"></div></div>
<script>window.LEVEL={{ n }};</script><script src="/static/level.js"></script>
<details><summary>Need a hint?</summary><p>{{ hint }}</p></details>
<p class="nav"><a href="/">← all levels</a></p>{% endif %}
</div></main></body></html>"""


def page(n, body, head="", status=200, headers=None, title=None):
    html = render_template_string(
        LAYOUT, n=n, title=title or LEVEL_TITLES.get(n, "Cherry's Birthday CTF"),
        body=body, head=head, hint=HINTS.get(n, ""))
    resp = make_response(html, status)
    for k, v in (headers or {}).items():
        resp.headers[k] = v
    return resp


def box(text):
    return '<pre class="flag">%s</pre>' % text


# ---------------------------------------------------------------- progress
def solved_levels():
    return set(int(x) for x in session.get("solved", []) if str(x).isdigit())


def progress():
    """Highest level N such that levels 1..N are all solved."""
    done, n = solved_levels(), 0
    while (n + 1) in done:
        n += 1
    return n


def locked_page(n):
    cur = progress() + 1
    body = ('<p>🔒 This level is locked. Solve level <b>%d</b> first and submit its flag.</p>'
            '<p><a href="/level/%d">Go to level %d →</a></p>') % (cur, cur, cur)
    return page(None, body, status=403, title="Locked")


def gate(n):
    """Return a locked response if level n isn't unlocked yet, else None."""
    if n > progress() + 1:
        return locked_page(n)
    return None


# ---------------------------------------------------------------- hub
@app.route("/")
def index():
    p = progress()
    cells = ""
    for i in range(1, 30):
        if i <= p:
            cells += '<a class="cell done" href="/level/%d"><b>%02d</b><span>%s</span></a>' % (i, i, LEVEL_TITLES[i])
        elif i == p + 1:
            cells += '<a class="cell open" href="/level/%d"><b>%02d</b><span>%s</span></a>' % (i, i, LEVEL_TITLES[i])
        else:
            cells += '<div class="cell locked"><b>%02d</b><span>🔒 locked</span></div>' % i
    body = """
<p>Happy Birthday! 🎂 There are <b>29 gifts</b> waiting for you. Each one is locked behind a level.
Solve a level, submit its flag on that level's page, and the gift opens along with the next level.</p>
<p>Flag format: <code>CherryBrdayGift{XX_YY}</code></p>
<p class="count"><b>%d</b> / 29 unlocked</p>
<a class="start" href="%s">%s</a>
<div class="grid">%s</div>
<h2>Your gifts</h2><div id="gifts"></div>
<script src="/static/hub.js"></script>""" % (p, ("/love" if p >= 29 else "/level/%d" % (p + 1)), "Continue → Level %d" % min(p + 1, 29) if p < 29 else "All done 🎉 Open your last surprise", cells)
    return page(None, body, title="Find the flags, open the gifts")


@app.route("/api/state")
def api_state():
    p = progress()
    return jsonify(progress=p, gifts={str(i): GIFTS.get(str(i), {"title": "Gift %d" % i, "message": ""})
                                      for i in range(1, p + 1)})


@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.get_json(silent=True) or {}
    try:
        n = int(data.get("level"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad level"), 400
    if n < 1 or n > 29 or n > progress() + 1:
        return jsonify(ok=False, error="locked"), 403
    if not hmac.compare_digest(str(data.get("flag", "")).strip(), flag(n)):
        return jsonify(ok=False)
    done = solved_levels()
    done.add(n)
    session.permanent = True
    session["solved"] = sorted(done)
    return jsonify(ok=True, level=n, next=(n + 1 if n < 29 else None),
                   gift=GIFTS.get(str(n), {"title": "Gift %d" % n, "message": ""}))


@app.route("/level/<int:n>", methods=["GET", "POST"])
def level(n):
    fn = LEVELS.get(n)
    if not fn:
        return page(None, "<p>No such level.</p>", title="404"), 404
    g = gate(n)
    if g:
        return g
    return fn()


# ---------------------------------------------------------------- levels
def l1():
    enc = base64.b64encode(flag(1).encode()).decode()
    return page(1, "<p>Here is a mysterious message:</p>" + box(enc))


def l2():
    body = "<p>Nothing to see here. Or is there?</p><!-- TODO remove before party: %s -->" % flag(2)
    return page(2, body)


def l3():
    return page(3, "<p>Even robots have rules. Humans... less so.</p>")


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /s3cr3t-cherry-vault\n", mimetype="text/plain")


@app.route("/s3cr3t-cherry-vault")
def vault():
    g = gate(3)
    if g:
        return g
    return page(None, "<p>You weren't supposed to be here, but fine:</p>" + box(flag(3)), title="Vault")


def l4():
    msg = ""
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE users(username TEXT, password TEXT)")
        db.execute("INSERT INTO users VALUES('admin', ?)", (secrets.token_hex(12),))
        db.execute("INSERT INTO users VALUES('cherry', ?)", (secrets.token_hex(12),))
        q = "SELECT username FROM users WHERE username='%s' AND password='%s'" % (u, p)
        try:
            row = db.execute(q).fetchone()
        except Exception as e:
            row, msg = None, '<p class="err">SQL error: %s<br><code>%s</code></p>' % (e, q.replace("<", "&lt;"))
        if row and row[0] == "admin":
            msg = box(flag(4))
        elif row:
            msg = "<p>Welcome, %s. But you're not the admin.</p>" % row[0]
        elif not msg:
            msg = '<p class="err">Wrong username or password.</p>'
    form = """<p>Admin login. You don't know the password. Obviously.</p>
<form method="post"><input name="username" placeholder="username">
<input name="password" placeholder="password" type="password"><button>Login</button></form>"""
    return page(4, form + msg)


def l5():
    return page(5, "<p>Decode me:</p>" + box(flag(5).encode().hex()))


def l6():
    import codecs
    return page(6, "<p>Decode me:</p>" + box(codecs.encode(flag(6), "rot13")))


def l7():
    role = request.cookies.get("role", "guest")
    body = "<p>Welcome, <b>%s</b>. Only admins get gifts here.</p>" % ("guest" if role != "admin" else "admin")
    if role == "admin":
        body += box(flag(7))
    resp = page(7, body)
    if "role" not in request.cookies:
        resp.set_cookie("role", "guest")
    return resp


def l8():
    enc = base64.b64encode(flag(8).encode()).decode()
    head = '<script>window.cherrySecret=atob("%s");console.log("Psst... have you looked at window.cherrySecret ?");</script>' % enc
    return page(8, "<p>This page looks empty. The browser's console might disagree.</p>", head=head)


def l9():
    return page(9, "<p>The flag isn't on the page. It's riding along with it.</p>",
                headers={"X-Cherry-Flag": flag(9)})


def l10():
    body = ""
    if request.method == "POST":
        if request.form.get("is_cherry") == "true":
            body = box(flag(10))
        else:
            body = '<p class="err">Sorry, you are not Cherry. Go away.</p>'
    form = """<p>Only Cherry may enter. The form already knows you aren't.</p>
<form method="post"><input type="hidden" name="is_cherry" value="false">
<button>I am Cherry</button></form>"""
    return page(10, form + body)


def l11():
    msg = ""
    if request.method == "POST":
        ok = all(request.form.get("q%d" % i, "").strip().lower() in
                 [a.lower() for a in q["answers"]] for i, q in enumerate(QUIZ))
        msg = box(flag(11)) if ok else '<p class="err">Not all answers are right. Try again!</p>'
    qs = "".join('<label>%d. %s<input name="q%d" autocomplete="off"></label>' % (i + 1, q["question"], i)
                 for i, q in enumerate(QUIZ))
    return page(11, '<form method="post">%s<button>Submit answers</button></form>%s' % (qs, msg))


def l12():
    codes = ",".join(str(ord(c)) for c in flag(12))
    head = """<script>
function check(){
  var v=document.getElementById('pw').value;
  if(v.split('').reverse().join('')==='6202yrrehc'){
    document.getElementById('out').textContent=String.fromCharCode(%s);
  } else {document.getElementById('out').textContent='Wrong password.';}
}</script>""" % codes
    body = """<p>Super secure password check.</p>
<input id="pw" placeholder="password"><button onclick="check()">Open</button>
<pre class="flag" id="out"></pre>"""
    return page(12, body, head=head)


@app.route("/config.php.bak")
def bak():
    g = gate(13)
    if g:
        return g
    txt = "<?php\n// backup of config - DELETE ME\n$db_user='cherry';\n$db_pass='hunter2';\n$gift_flag='%s';\n" % flag(13)
    return Response(txt, mimetype="text/plain")


def l13():
    return page(13, "<p>Developers are human. They leave things behind.</p>")


def l14():
    i = request.args.get("id", "5")
    notes = {"5": "Your gift: a very nice virtual high-five 🖐️", "2": "Gift #2: nothing, it is just a number.",
             "3": "Gift #3: Free hug (redeemable in person).", "4": "Gift #4: a rubber duck 🦆", "1": box(flag(14))}
    body = "<p>You are viewing gift <b>id=%s</b>.</p>%s" % (
        i.replace("<", "&lt;"), notes.get(i, "<p>No gift with that id.</p>"))
    return page(14, body)


def l15():
    if request.args.get("debug") == "true":
        return page(15, "<p>Debug mode ON.</p>" + box(flag(15)))
    return page(15, "<p>Debug mode is off.</p>")


@app.route("/admin")
def admin():
    g = gate(16)
    if g:
        return g
    return page(None, "<p>Admin panel. You found it.</p>" + box(flag(16)), title="Admin")


def l16():
    return page(16, "<p>The boss has an office. Every website has one.</p>")


def l17():
    head = "<style>.ink{color:#14090f;background:#14090f;user-select:text}</style>"
    return page(17, '<p>Nothing here...</p><p class="ink">%s</p>' % flag(17), head=head)


MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
         "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
         "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
         "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
         "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.", "_": "..--.-"}


def inner(n):
    return flag(n)[len("CherryBrdayGift{"):-1]


def l18():
    chart = " &nbsp; ".join("<b>%s</b> %s" % (k, v) for k, v in MORSE.items())
    return page(18, "<p>Decode this morse (letters are separated by spaces). Put the answer inside "
                    "<code>CherryBrdayGift{ }</code>.</p>" + box(" ".join(MORSE[c] for c in inner(18))) +
                "<details><summary>Morse chart</summary><p>%s</p></details>" % chart)


def l19():
    return page(19, "<p>Decode this. Put the answer inside <code>CherryBrdayGift{ }</code>.</p>" +
                box(" ".join(format(ord(c), "08b") for c in inner(19))))


@app.route("/assets/cherry.css")
def css20():
    g = gate(20)
    if g:
        return g
    css = "/* Cherry theme */\nbody{background:#14090f}\n/* secret: %s */\n" % flag(20)
    return Response(css, mimetype="text/css")


def l20():
    return page(20, '<p>This page is dressed up by a stylesheet. Maybe the designer left something in it...</p>',
                head='<link rel="stylesheet" href="/assets/cherry.css">')


def l21():
    b64 = base64.b64encode(flag(21).encode()).decode()
    head = '<script>try{localStorage.setItem("cherryGift",atob("%s"))}catch(e){}</script>' % b64
    return page(21, "<p>This page quietly put something in your pocket (your browser's storage). Go find it.</p>",
                head=head)


def l22():
    b64 = base64.b64encode(flag(22).encode()).decode()
    head = ('<script>function openIt(){document.getElementById("out").textContent=atob("%s");}</script>' % b64)
    body = ('<p>The button is disabled. Convince it otherwise.</p>'
            '<button id="b" disabled onclick="openIt()">Reveal the gift</button>'
            '<pre class="flag" id="out"></pre>')
    return page(22, body, head=head)


@app.route("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?><urlset>'
           '<url><loc>/</loc></url><url><loc>/hidden-gift-23</loc></url></urlset>')
    return Response(xml, mimetype="application/xml")


@app.route("/hidden-gift-23")
def hidden23():
    g = gate(23)
    if g:
        return g
    return page(None, box(flag(23)), title="You found the sitemap secret")


def l23():
    return page(23, "<p>Crawlers like lists of pages.</p>")


@app.route("/humans.txt")
def humans():
    g = gate(24)
    if g:
        return g
    return Response("/* TEAM */\nBuilder: someone who loves Cherry\n\n/* SECRET */\n%s\n" % flag(24),
                    mimetype="text/plain")


def l24():
    return page(24, "<p>Robots get <code>robots.txt</code>. Humans get something too...</p>")


def l25():
    name = request.args.get("name", "")
    low = name.lower()
    out = "<p>Hello, %s!</p>" % name  # intentionally unsanitised
    if "alert(" in low and ("<script" in low or "onerror" in low or "onload" in low):
        out += "<p>🤖 The bot saw your alert and surrendered:</p>" + box(flag(25))
    form = '<form method="get"><input name="name" placeholder="your name"><button>Greet me</button></form>'
    return page(25, form + out)


VFS = {"/app/public/welcome.txt": "Welcome! Files here are public.",
       "/app/public/readme.txt": "Public files live in /app/public. Secret stuff lives in /app/secret.",
       "/app/secret/flag.txt": flag(26)}


def l26():
    name = request.args.get("name", "welcome.txt")
    path = posixpath.normpath(posixpath.join("/app/public", name))
    content = VFS.get(path, "File not found: %s" % path.replace("<", "&lt;"))
    return page(26, "<p>File viewer: <code>?name=welcome.txt</code>. Public files live in /app/public, "
                    "secret stuff lives in /app/secret.</p><pre>%s</pre>" % content.replace("<", "&lt;"))


def l27():
    return page(27, "<p>Someone wrote this the wrong way round:</p>" + box(flag(27)[::-1]))


def l28():
    b64 = base64.b64encode(flag(28).encode()).decode()
    head = """<script>
var clicks=0;
function cherry(){clicks++;document.getElementById('c').textContent=clicks+' / 5';
 if(clicks>=5){document.getElementById('out').textContent=atob("%s");}}
</script>""" % b64
    body = ('<p>Give the cherry some love.</p>'
            '<p style="font-size:4rem;cursor:pointer;margin:6px 0" onclick="cherry()">🍒</p>'
            '<p id="c">0 / 5</p><pre class="flag" id="out"></pre>')
    return page(28, body, head=head)


def l29():
    f = flag(29)
    k = len(f) // 3
    p1, p2, p3 = f[:k], f[k:2 * k], f[2 * k:]
    head = '<script>console.log("PART 2 of 3: %s");</script>' % p2
    body = ('<p>The flag is split into <b>3 pieces</b>, each hidden with a trick you already know. '
            'Join them in order: part 1 + part 2 + part 3.</p>'
            '<p>Part 1: somewhere in the page source. Part 2: in the console. Part 3: in the response headers.</p>'
            '<!-- PART 1 of 3: %s -->' % p1)
    return page(29, body, head=head, headers={"X-Part-3": "PART 3 of 3: %s" % p3})


PHOTO_DIR = os.path.join(HERE, "photos")
PHOTO_SLOTS = [("him1", "Handsome", "tilt-l"), ("us1", "Us", "tilt-r"),
               ("us2", "Us again", "tilt-l"), ("him2", "My favourite human", "tilt-r")]


def find_photo(stem):
    for ext in ("jpg", "jpeg", "png", "webp", "JPG", "JPEG", "PNG"):
        if os.path.exists(os.path.join(PHOTO_DIR, "%s.%s" % (stem, ext))):
            return "%s.%s" % (stem, ext)
    return None


@app.route("/photo/<name>")
def photo(name):
    if progress() < 29:
        return locked_page(29)
    stem = os.path.splitext(name)[0]
    real = find_photo(stem) if stem in dict((a, b) for a, b, _ in PHOTO_SLOTS) else None
    if not real:
        return Response("not found", status=404)
    return send_from_directory(PHOTO_DIR, real)


@app.route("/love")
def love():
    if progress() < 29:
        return locked_page(29)
    try:
        with open(os.path.join(HERE, "letter.txt"), encoding="utf-8") as f:
            letter = f.read().strip()
    except OSError:
        letter = ""
    from markupsafe import escape
    paras = "".join("<p>%s</p>" % str(escape(p)).replace("\n", "<br>") for p in letter.split("\n\n") if p.strip())
    figs = ""
    for stem, cap, tilt in PHOTO_SLOTS:
        real = find_photo(stem)
        img = ('<img src="/photo/%s" alt="%s">' % (real, cap)) if real else '<div class="ph">📷<br>add photo</div>'
        figs += '<figure class="polaroid %s">%s<figcaption>%s</figcaption></figure>' % (tilt, img, cap)
    body = ('<div class="love"><div class="hearts">💗 🍒 💗</div>'
            '<h2 class="big">I love you, Anup</h2>'
            '<div class="photos">%s</div>'
            '<div class="letter">%s</div>'
            '<p class="hearts">💗 Happy Birthday 💗</p></div>') % (figs, paras)
    return page(None, body, title="One last thing...")


LEVELS = {1: l1, 2: l2, 3: l3, 4: l4, 5: l5, 6: l6, 7: l7, 8: l8, 9: l9, 10: l10, 11: l11, 12: l12,
          13: l13, 14: l14, 15: l15, 16: l16, 17: l17, 18: l18, 19: l19, 20: l20, 21: l21, 22: l22,
          23: l23, 24: l24, 25: l25, 26: l26, 27: l27, 28: l28, 29: l29}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
