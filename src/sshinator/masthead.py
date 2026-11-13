"""The SSHinator masthead, borrowed from sshm. Kept as a constant because the
archived masthead.md in the vault is not shipped with the package."""

LOGO_LINES = (
    r" _______ _______ _______ __               __",
    r"|     __|     __|   |   |__|.-----.---.-.|  |_.-----.----.",
    r"|__     |__     |       |  ||     |  _  ||   _|  _  |   _|",
    r"|_______|_______|___|___|__||__|__|___._||____|_____|__|",
)
LOGO = "\n".join(LOGO_LINES)
SHORT_HEADER = "SSHinator"
# Terminal height below which the one-line header is used so 80x24 layouts still fit.
MIN_HEIGHT_FOR_LOGO = 20

HELP_ITEMS = (
    "select: ↑/↓",
    "connect: ENTER",
    "expand/details: SPACE",
    "edit: e",
    "search: /",
    "clear/quit: ESC",
    "reload: CTRL+R",
    "tabs: ←/→",
    "q quit",
)
