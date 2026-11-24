# Cherry's Birthday CTF 🍒

29 levels, 29 gifts. Flag format: `CherryBrdayGift{NN_TAG}`.

## Run it

```bash
pip install -r requirements.txt
python app.py              # http://localhost:5000
# or for hosting:
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

Easy free hosts: Render, Railway, PythonAnywhere, Fly.io (start command: `gunicorn app:app`).

## Customise

- `gifts.json` : the text revealed when each level is cleared (your 29 gift descriptions are already in).
- `quiz.json` : level 11 questions and accepted answers (case-insensitive).
- Flag codes: edit `TAGS` at the top of `app.py` (all 29 are your real codes now).

## Notes

- Keep `app.py` private. The flags live in it, so don't put it in a public repo.
- Levels unlock in order, enforced on the server. Each level page has its own flag box; progress is kept in a signed cookie (1 year), so he can come back on the same device.
- Set a `SECRET_KEY` environment variable when hosting so progress survives restarts (otherwise a `.secret_key` file is created next to `app.py`).
- The SQLi (level 4) runs on a throwaway in-memory database with no real data. The XSS (level 25) only
  reflects into the page of whoever types it. Nothing here touches real files or other users.
- Hint: `SOLUTIONS.md` has every solve path, don't send it to him 😄

## Final page (/love)

Opens only after level 29. Put 4 photos in `photos/` named `him1`, `him2`, `us1`, `us2` (jpg, jpeg, png or webp). Empty slots show an "add photo" box. Edit the letter in `letter.txt` (blank line = new paragraph). Photos are served only to people who finished level 29.
