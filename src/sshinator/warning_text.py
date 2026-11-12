"""Every user-facing string for the safe_mode and dont-blame boxes. Edit wording here only."""

from pathlib import Path

SAFE_MODE = "safe_mode"
DONT_BLAME = "dont_blame"
SAFE_WORD = "safe"  # content of the acceptance file when safe is the default

# Author's wording, kept exactly. Shown directly above the backup lines.
BUG_MESSAGE = (
    "Due to a software BUG, The SSHinator is creating a shadow backup file. "
    "We've provided the path to the file so you can delete it manually. "
    "Our sincerest apologies."
)

SHADOW_TITLE = "*** WARNING ***"
SHADOW_CONTINUE = "Continue"
SHADOW_CANCEL = "Cancel"

BLAME_TITLE = "*** ADVANCED MODE ***"
BLAME_ACCEPT = "Accept"
BLAME_DECLINE = "Decline"
BLAME_TEXT = """\
You are about to take the safety off.

With --dont-blame-doofenshmirtz, the SSHinator will no longer warn you before it overwrites your ssh config. A backup is still made, but nothing stops you before the write.

If something goes wrong, do not blame Dr. Doofenshmirtz. This one is on you.
"""
BLAME_DECLINED_TOAST = "Declined. Running in safe_mode."

GATE_REQUIRED = (
    "--dont-blame-doofenshmirtz needs the warning gate accepted first. "
    "Run sshinator once without it."
)



def shadow_text(config: Path, backup_dir: Path, backup_name: str) -> str:
    return (
        "A destructive action is about to occur.\n\n"
        f"File to be overwritten: {config}\n\n"
        f"{BUG_MESSAGE}\n\n"
        f"Backup folder: {backup_dir}\n"
        f"Backup file: {backup_name}"
    )


