# Module 5 — Draft, approve, publish

This is the only module that changes anything on Instagram. Re-read `safety-rules.md` before starting.

## 1. Draft
Write `instagram-data/drafts/YYYY-MM-DD-<slug>.md` from `templates/post-draft.md` with:
- **Media:** exact file path(s) on the user's computer, order for carousels, crop/aspect ratio (1:1, 4:5, 9:16), cover frame for Reels. The skill does not create media; the user supplies it. If none is supplied, propose a shot list and stop.
- **Caption:** full text, final form.
- **Hashtags:** the exact list and where they go (caption end or first comment).
- **Alt text:** for every image (plain description of what's in it, ≤ ~100 words; for screenshots, the key text).
- **Location tag, collaborators, product tags:** only if the user asked for them.
- **Claims check:** list each factual claim in the caption and confirm it is allowed by `profile.md`.

## 2. Show in full and wait
Show the user the complete draft in the chat — every word of the caption, every hashtag, every alt text, every media file and its order. Then ask: **"Post this exactly as shown? (yes / changes)"**
Do nothing on Instagram until the answer is an unambiguous yes. Any change → update the draft file → show the whole thing again → new yes.

## 3. Publish (only after yes)
1. In the working tab, click Create / "+" → Post (or Reel).
2. Upload the media: the file picker is a native OS dialog that the extension may not be able to drive. If it can't, ask the user to select the file(s) themselves in the dialog and tell you when done. Never substitute different media.
3. Apply the agreed crop. Add alt text via "Advanced settings → Write alt text" (or "Accessibility").
4. Paste the caption exactly as approved. Compare the text in the box against the draft before continuing.
5. **Before clicking Share**, take a screenshot of the final screen and show it to the user if anything differs from the approved draft (truncated caption, wrong crop, missing alt text). If it differs, fix it or stop — don't share.
6. Click Share once. Never click it twice. If it seems to hang, wait and check the profile rather than clicking again.
7. If any hard-stop message appears (see `safety-rules.md`), stop.

## 4. Confirm
- Open the profile, find the new post, open it, and copy its URL (`https://www.instagram.com/p/<code>/` or `/reel/<code>/`).
- Check the caption and alt text published correctly.
- Tell the user it's live with the link. Update the draft file with `status: published`, the URL and the time. Append to `log.md`.
- If you can't find the post, say so honestly. Don't claim it went live.
