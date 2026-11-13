"""Command-line entry point: ``sshinator [--config PATH]``."""

import argparse
import sys
from pathlib import Path

from . import paths, warning_text
from .app import SSHinator


def main() -> None:
    parser = argparse.ArgumentParser(prog="sshinator", description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="ssh config file to manage (default: ~/.ssh/config)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="forget the earlier acceptance, so the warning shows again",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--dont-blame-doofenshmirtz",
        action="store_true",
        help="advanced: turn off the shadow-backup warning before writes (asks once to confirm)",
    )
    modes.add_argument(
        "--safe",
        action="store_true",
        help="start in safe_mode and delete the unsafe acceptance file, so unsafe must be asked for again",
    )
    parser.add_argument(
        "--accept",
        action="store_true",
        help="accept the startup warning without starting the app (cannot be combined with other options)",
    )
    args = parser.parse_args()
    if args.accept and (args.config is not None or args.reset or args.dont_blame_doofenshmirtz or args.safe):
        parser.error("--accept cannot be combined with any other option")
    if args.safe and args.reset:
        parser.error("--safe cannot be combined with --reset")
    if args.accept:
        marker = paths.accept_marker()
        if marker.exists():
            print(f"The warning is already accepted: {marker}")
        else:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("accepted\n", encoding="utf-8")
            print(f"Accepted. The warning will not show again: {marker}")
        return
    config = (args.config or paths.default_config()).expanduser()
    if args.reset:
        removed = False
        for marker, what in (
            (paths.accept_marker(), "The warning will show again"),
            (paths.blame_marker(), "The dont-blame-doofenshmirtz box will show again"),
        ):
            if marker.exists():
                marker.unlink()
                removed = True
                print(f"Reset. {what}: {marker}")
        if not removed:
            print("Nothing to reset. The warning has not been accepted yet.")
        return
    if args.dont_blame_doofenshmirtz and not paths.accept_marker().exists():
        print(warning_text.GATE_REQUIRED, file=sys.stderr)
        sys.exit(2)
    SSHinator(config, dont_blame=args.dont_blame_doofenshmirtz, safe=args.safe).run()


if __name__ == "__main__":
    main()
