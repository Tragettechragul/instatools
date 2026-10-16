# Module 1 — Pull my data

Read-only. Output: `instagram-data/insights/YYYY-MM-DD-account.md` (from `templates/account-insights.md`) and `instagram-data/insights/YYYY-MM-DD-posts.csv` (from `templates/posts.csv`).

## Where things are on instagram.com
Instagram moves these often — if a path isn't there, look for it with `find`/`read_page` rather than guessing URLs, and note the actual location in the log.
- Professional dashboard: profile → "Professional dashboard", or `https://www.instagram.com/accounts/insights/`
- Per-post insights: open a post → "View insights" (only on your own posts)
- The web dashboard is thinner than the mobile app. Anything missing is recorded as `NOT AVAILABLE ON WEB` and listed in the summary so the user can screenshot it from the app and paste it in.

## Steps
1. **Account overview.** For each period selector offered (7 / 30 / 90 days — use whatever options exist): reach (accounts reached), views, profile visits, follower change (net, plus follows/unfollows if shown), accounts engaged. Record the exact date range Instagram displays next to each.
2. **Recent posts.** From the profile grid, open each post from the last 90 days (cap at 30). For each, record: format (Reel / carousel / single image), posted date, full caption, views, likes, comments, saves, shares, reach if shown. Close the post before opening the next. Append to the CSV after each post.
3. **Audience.** From the followers/audience section: top cities, top countries, age ranges, gender split, most active hours, most active days.

## Analysis (write into the account file)
Only after collecting. Always state sample size.
- **Which format wins:** median (not mean — one viral post skews means) views and engagement per format. Engagement = likes + comments + saves + shares. Also engagement rate = engagement ÷ views where views exist.
- **Which times win:** group posts by weekday and by 3-hour posting window; compare medians; cross-check with the "most active" audience times. With fewer than ~10 posts, say the pattern is not reliable yet.
- **Trend:** compare 7 vs 30 vs 90-day rates (per-day reach, profile visits, follower change). Say up / flat / down, with the numbers.
- **Plain-English summary:** 3–5 bullet points the user can act on.
