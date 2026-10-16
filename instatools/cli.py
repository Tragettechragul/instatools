import argparse
import json
import logging
import sys
from pathlib import Path

from . import captioner, config, poster, puller, watcher
from .browser import interactive_login, logged_in_username, session
from .guards import HardStop, NotLoggedIn


def _setup_logging(cfg: config.Config) -> None:
    fmt = "%(asctime)s %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt,
                        handlers=[logging.StreamHandler(), logging.FileHandler(cfg.log_file, encoding="utf-8")])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="instatools", description="Automate your own Instagram account.")
    ap.add_argument("--home", help="data directory (default ./data or $INSTATOOLS_HOME)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login", help="open a browser and log in by hand once; the session is saved")
    sub.add_parser("whoami", help="show which account the saved session is logged in as")

    w = sub.add_parser("watch", help="post everything dropped into data/inbox, automatically")
    w.add_argument("--once", action="store_true", help="process the inbox once and exit (for cron / Task Scheduler)")
    w.add_argument("--poll", type=int, default=30, help="seconds between inbox checks")

    p = sub.add_parser("post", help="post files right now")
    p.add_argument("files", nargs="+", type=Path, help="1 file, or up to 10 for a carousel")
    p.add_argument("--caption", help="exact caption (otherwise a same-name .txt, then Claude)")

    pl = sub.add_parser("pull", help="download posts, captions, stats and audio from a profile")
    pl.add_argument("username", nargs="?", help="profile to pull (default: your own)")
    pl.add_argument("--limit", type=int, default=12)
    pl.add_argument("--transcribe", action="store_true", help="speech-to-text on videos (needs faster-whisper)")

    r = sub.add_parser("get", help="download one post or Reel by URL")
    r.add_argument("url")
    r.add_argument("--transcribe", action="store_true")

    args = ap.parse_args(argv)
    cfg = config.load(args.home)
    _setup_logging(cfg)

    try:
        if args.cmd == "login":
            interactive_login(cfg)
        elif args.cmd == "whoami":
            with session(cfg) as page:
                print("@" + logged_in_username(page))
        elif args.cmd == "watch":
            watcher.run(cfg, once=args.once, poll=args.poll)
        elif args.cmd == "post":
            files = [f.resolve() for f in args.files]
            note = files[0].with_suffix(".txt")
            text = captioner.PostText(args.caption) if args.caption else captioner.build(cfg, files, note if note.exists() else None)
            with session(cfg) as page:
                print(poster.publish(page, files, text))
        elif args.cmd == "pull":
            with session(cfg) as page:
                user = args.username or logged_in_username(page)
                for folder in puller.pull_profile(page, cfg, user, args.limit, args.transcribe):
                    print(folder)
        elif args.cmd == "get":
            with session(cfg) as page:
                folder = puller.pull_post(page, cfg, args.url, do_transcribe=args.transcribe)
                print(json.dumps(json.loads((folder / "post.json").read_text()), indent=2, ensure_ascii=False))
    except HardStop as e:
        cfg.stop_file.write_text(f"HardStop: {e}\n")
        logging.error("STOPPED — %s. Not retrying; deal with it in Instagram, then delete %s", e, cfg.stop_file)
        return 2
    except NotLoggedIn as e:
        logging.error("%s", e)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
