"""The Textual interface: a single Hosts tab with groups, search, and an edit form."""

import re
import subprocess
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList, Select, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option, OptionDoesNotExist

from . import paths, sshconfig, warning_text
from .knownhosts import default_known_hosts, read_known_hosts
from .masthead import HELP_ITEMS, LOGO, MIN_HEIGHT_FOR_LOGO, SHORT_HEADER
from .sshconfig import HostEntry, SshConfig

STRICT_CHOICES = [("yes", "yes"), ("no", "no"), ("accept-new", "accept-new")]
UNGROUPED = "Ungrouped"
CONFIRM_TEXT = """\
config file found: {config}

Ah-ha! Behold, my latest weapon of reasonable destruction.

THE SSHinator!

It all started back in the Gimmelshtump School For The Orphans when I had to connect my broken abacus to the high-voltage telegraph lines and type out IP addresses by hand. Could you believe that?! My fingers are still tingling!

BUT THOSE DAYS ARE OVER!

Every time you save, the SSHinator will warn you before it obliterates your current ssh-config, zapping a backup straight to the shadow lands of {backups}. Only the last 20 are kept, though—evil lair storage isn't cheap, you know. You can always hit the self-destruct—er, cancel button.

NOW, I, Dr. Heinz Doofenshmirtz, shall take over the entire Tri-State Area one config at a time...

STARTING WITH YOURS!

Curse you
"""


class GateScreen(ModalScreen[bool]):
    """One-time confirmation before SSHinator may write to the config."""

    BINDINGS = [
        Binding("escape", "decline", "Quit", show=False),
        # Priority, so the arrows reach the gate before the scroll container uses them.
        Binding("left", "focus_accept", show=False, priority=True),
        Binding("right", "focus_quit", show=False, priority=True),
    ]

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path

    def compose(self) -> ComposeResult:
        text = CONFIRM_TEXT.format(
            config=self.config_path,
            backups=paths.backup_dir(),
        )
        with VerticalScroll(id="dialog"):
            yield Static("*** WARNING ***", classes="title warning")
            yield Static(text)
            with Horizontal(classes="buttons"):
                yield Button("Accept", variant="primary", id="accept")
                yield Button("Quit", id="decline")

    def on_mount(self) -> None:
        # Quit has focus, so an accidental Enter does not accept the warning.
        self.action_focus_quit()

    def action_focus_accept(self) -> None:
        self.query_one("#accept", Button).focus()

    def action_focus_quit(self) -> None:
        self.query_one("#decline", Button).focus()

    @on(Button.Pressed, "#accept")
    def accept(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#decline")
    def action_decline(self) -> None:
        self.dismiss(False)


class ShadowBackupScreen(ModalScreen[bool]):
    """Safe-mode warning shown before a write replaces the file."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, config_path: Path, backup_name: str) -> None:
        super().__init__()
        self.config_path = config_path
        self.backup_name = backup_name

    def compose(self) -> ComposeResult:
        text = warning_text.shadow_text(self.config_path, paths.backup_dir(), self.backup_name)
        with VerticalScroll(id="dialog"):
            yield Static(warning_text.SHADOW_TITLE, classes="title warning")
            yield Static(text)
            with Horizontal(classes="buttons"):
                yield Button(warning_text.SHADOW_CONTINUE, variant="primary", id="continue")
                yield Button(warning_text.SHADOW_CANCEL, id="cancel")

    def on_mount(self) -> None:
        # Cancel has focus, so an accidental Enter does not continue.
        self.query_one("#cancel", Button).focus()

    @on(Button.Pressed, "#continue")
    def proceed(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self) -> None:
        self.dismiss(False)


class BlameScreen(ModalScreen[bool]):
    """Second box: accept turning the safe_mode warning off."""

    BINDINGS = [
        Binding("escape", "decline", "Decline", show=False),
        Binding("left", "focus_accept", show=False, priority=True),
        Binding("right", "focus_decline", show=False, priority=True),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="dialog"):
            yield Static(warning_text.BLAME_TITLE, classes="title warning")
            yield Static(warning_text.BLAME_TEXT)
            with Horizontal(classes="buttons"):
                yield Button(warning_text.BLAME_ACCEPT, variant="primary", id="accept")
                yield Button(warning_text.BLAME_DECLINE, id="decline")

    def on_mount(self) -> None:
        self.action_focus_decline()

    def action_focus_accept(self) -> None:
        self.query_one("#accept", Button).focus()

    def action_focus_decline(self) -> None:
        self.query_one("#decline", Button).focus()

    @on(Button.Pressed, "#accept")
    def accept(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#decline")
    def action_decline(self) -> None:
        self.dismiss(False)


class EditScreen(ModalScreen[dict | None]):
    """A flat form with the fields v1 manages."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, entry: HostEntry) -> None:
        super().__init__()
        self.entry = entry
        self.options = entry.block.options()

    def compose(self) -> ComposeResult:
        current = self.options
        strict = current.get("StrictHostKeyChecking", "")
        with VerticalScroll(id="dialog"):
            yield Static(f"Edit {self.entry.alias}", classes="title")
            yield Label("Host (alias)")
            yield Input(self.entry.alias, id="alias")
            yield Label("HostName")
            yield Input(current.get("HostName", ""), id="HostName")
            yield Label("User")
            yield Input(current.get("User", ""), id="User")
            yield Label("Port")
            yield Input(current.get("Port", ""), id="Port", type="integer")
            yield Label("IdentityFile")
            yield Input(current.get("IdentityFile", ""), id="IdentityFile")
            yield Label("ProxyJump")
            yield Input(current.get("ProxyJump", ""), id="ProxyJump")
            yield Label("StrictHostKeyChecking")
            yield Select(
                STRICT_CHOICES,
                value=strict if strict else Select.NULL,
                allow_blank=True,
                id="StrictHostKeyChecking",
            )
            yield Static("", id="error", classes="warning")
            with Horizontal(classes="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        alias = self.query_one("#alias", Input).value.strip()
        if not alias or any(char.isspace() for char in alias):
            self.query_one("#error", Static).update(
                "Alias must be one name, with no spaces."
            )
            return
        port = self.query_one("#Port", Input).value.strip()
        if port and not (port.isdigit() and 0 < int(port) < 65536):
            self.query_one("#error", Static).update("Port must be 1 to 65535.")
            return
        values = {
            key: self.query_one(f"#{key}", Input).value.strip()
            for key in ("HostName", "User", "Port", "IdentityFile", "ProxyJump")
        }
        strict = self.query_one("#StrictHostKeyChecking", Select).value
        values["StrictHostKeyChecking"] = "" if strict is Select.NULL else str(strict)
        self.dismiss({"alias": alias, "values": values})

    @on(Button.Pressed, "#cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)


class SSHinator(App):
    TITLE = "SSHinator"
    CSS = """
    Screen { layers: base modal; }
    #masthead { padding: 0 1; text-style: bold; height: auto; }
    #masthead.mode-safe { color: $primary; }
    #masthead.mode-blame { color: #ff0000; }
    #search { display: none; height: 1; border: none; padding: 0 1; }
    #tabbed { height: 1fr; }
    TabPane { padding: 0; }
    #hosts { height: 1fr; }
    #help { border: round $primary; height: auto; padding: 0 1; }
    #dialog {
        width: 70%; max-width: 100; height: auto; max-height: 90%;
        border: round $accent; padding: 1 2; background: $surface;
    }
    .title { text-style: bold; margin-bottom: 1; }
    .warning { color: $warning; margin: 1 0; }
    .diff { margin-top: 1; }
    .buttons { height: auto; margin-top: 1; }
    .buttons Button { margin-right: 2; }
    GateScreen, ShadowBackupScreen, BlameScreen, EditScreen { align: center middle; }
    GateScreen #dialog, BlameScreen #dialog { width: 90%; }
    """

    BINDINGS = [
        Binding("space", "toggle", "Expand", show=False),
        Binding("e", "edit", "Edit", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("escape", "escape", "Clear / quit", show=False),
        Binding("ctrl+r", "reload", "Reload", show=False),
        Binding("q", "quit", "Quit", show=False),
        Binding("left", "prev_tab", "Previous tab", show=False),
        Binding("right", "next_tab", "Next tab", show=False),
    ]

    TAB_IDS = ("tab-hosts", "tab-known")

    def __init__(
        self, config_path: Path, known_hosts: Path | None = None,
        dont_blame: bool = False,
        safe: bool = False,
    ) -> None:
        super().__init__()
        self.dont_blame_requested = dont_blame
        self.safe_requested = safe
        self.mode = warning_text.SAFE_MODE
        self.config_path = config_path
        self.known_hosts_path = known_hosts or default_known_hosts()
        self.config = SshConfig([])
        self.file_text = ""
        self.expanded: set[str] = set()
        self.collapsed: set[str] = set()
        self.filter_text = ""

    # --- setup ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static(
            self._masthead_text(self.size.height or 50),
            id="masthead",
            classes=_mode_class(self.mode),
        )
        yield Input(placeholder="search alias or HostName", id="search")
        with TabbedContent(id="tabbed"):
            with TabPane("Hosts", id="tab-hosts"):
                yield OptionList(id="hosts")
            with TabPane("Known hosts", id="tab-known"):
                yield OptionList(id="known")
        yield Static(help_text(), id="help")

    @staticmethod
    def _masthead_text(height: int) -> str:
        return LOGO if height >= MIN_HEIGHT_FOR_LOGO else SHORT_HEADER

    def on_resize(self, event) -> None:
        try:
            self.query_one("#masthead", Static).update(self._masthead_text(event.size.height))
        except Exception:
            pass

    def on_mount(self) -> None:
        self.load()
        self.load_known_hosts()
        if not paths.accept_marker().exists():
            self.push_screen(GateScreen(self.config_path), self._after_gate)
        else:
            self._start_blame_check()

    def _after_gate(self, accepted: bool | None) -> None:
        if not accepted:
            self.exit()
            return
        marker = paths.accept_marker()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("accepted\n", encoding="utf-8")
        self._start_blame_check()

    def _start_blame_check(self) -> None:
        # Nothing here has an effect unless the gate marker exists, even if called directly.
        if paths.accept_marker().exists():
            marker = paths.blame_marker()
            if self.safe_requested:
                self._set_mode(warning_text.SAFE_MODE)
                # --safe removes the acceptance file, so unsafe must be asked for again.
                marker.unlink(missing_ok=True)
            elif self.dont_blame_requested:
                # The flag always asks, even when the file already exists.
                self.push_screen(BlameScreen(), self._after_blame)
                return
            elif marker.exists():
                # Old files hold "accepted": anything but "safe" means dont_blame.
                saved = marker.read_text(encoding="utf-8").strip()
                self._set_mode(
                    warning_text.SAFE_MODE if saved == warning_text.SAFE_WORD else warning_text.DONT_BLAME
                )
        self.query_one("#hosts", OptionList).focus()

    def _after_blame(self, accepted: bool | None) -> None:
        if accepted:
            marker = paths.blame_marker()
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(warning_text.DONT_BLAME + "\n", encoding="utf-8")
            self._set_mode(warning_text.DONT_BLAME)
        else:
            self.notify(warning_text.BLAME_DECLINED_TOAST)
        self.query_one("#hosts", OptionList).focus()

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        masthead = self.query_one("#masthead", Static)
        masthead.set_classes(_mode_class(mode))

    # --- loading and rendering ------------------------------------------

    def load(self) -> None:
        text = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else ""
        self.file_text = text
        self.config = SshConfig.parse(text)
        self.render_list()

    def render_list(self) -> None:
        option_list = self.query_one("#hosts", OptionList)
        highlighted = None
        if option_list.highlighted is not None:
            highlighted = option_list.get_option_at_index(option_list.highlighted).id
        options = self.build_options()
        option_list.clear_options()
        option_list.add_options(options)
        if highlighted is not None:
            index = option_list.get_option_index(highlighted) if _has(option_list, highlighted) else None
            if index is not None:
                option_list.highlighted = index
        elif options:
            option_list.highlighted = 0

    def build_options(self) -> list[Option]:
        hosts = self.config.hosts()
        if self.filter_text:
            return [self._host_option(entry, prefix="  ", suffix=f"  [{entry.group or UNGROUPED}]")
                    for entry in hosts if _fuzzy(self.filter_text, entry)]

        groups: dict[str, list[HostEntry]] = {}
        for entry in hosts:
            groups.setdefault(entry.group or UNGROUPED, []).append(entry)
        names = [name for name in groups if name != UNGROUPED]
        if UNGROUPED in groups:
            names.append(UNGROUPED)

        options: list[Option] = []
        for name in names:
            is_open = f"group:{name}" not in self.collapsed
            arrow = "▾" if is_open else "▸"
            options.append(Option(f"{arrow} {name}", id=f"group:{name}"))
            if not is_open:
                continue
            for entry in groups[name]:
                options.extend(self._host_rows(entry))
        return options

    def _host_rows(self, entry: HostEntry) -> list[Option]:
        is_open = f"host:{entry.alias}" in self.expanded
        arrow = "▾" if is_open else "▸"
        rows = [self._host_option(entry, prefix=f"  {arrow} ")]
        if is_open:
            for key, value in entry.block.options().items():
                rows.append(Option(f"        {key}: {value}", id=f"detail:{entry.alias}:{key}", disabled=True))
        return rows

    def _host_option(self, entry: HostEntry, prefix: str, suffix: str = "") -> Option:
        shown = entry.alias if entry.hostname == entry.alias else f"{entry.hostname} ({entry.alias})"
        label = f"{prefix}{shown}{suffix}"
        return Option(label, id=f"host:{entry.alias}")

    # --- actions --------------------------------------------------------

    def _highlighted_id(self) -> str | None:
        option_list = self.query_one("#hosts", OptionList)
        if option_list.highlighted is None:
            return None
        return option_list.get_option_at_index(option_list.highlighted).id

    def _entry_for(self, option_id: str | None) -> HostEntry | None:
        if not option_id or not option_id.startswith("host:"):
            return None
        alias = option_id.removeprefix("host:")
        return next((entry for entry in self.config.hosts() if entry.alias == alias), None)

    def _on_hosts_tab(self) -> bool:
        return self.query_one(TabbedContent).active == "tab-hosts"

    def load_known_hosts(self) -> None:
        known = self.query_one("#known", OptionList)
        known.clear_options()
        entries = read_known_hosts(self.known_hosts_path)
        if not entries:
            known.add_option(Option("No known hosts yet", disabled=True))
            return
        for entry in entries:
            prefix = f"{entry.marker} " if entry.marker else ""
            known.add_option(Option(f"{prefix}{entry.hosts}  {entry.key_type}"))

    def action_prev_tab(self) -> None:
        self._switch_tab(-1)

    def action_next_tab(self) -> None:
        self._switch_tab(1)

    def _switch_tab(self, step: int) -> None:
        tabbed = self.query_one(TabbedContent)
        index = self.TAB_IDS.index(tabbed.active)
        tabbed.active = self.TAB_IDS[(index + step) % len(self.TAB_IDS)]
        focus_id = "#hosts" if tabbed.active == "tab-hosts" else "#known"
        self.query_one(focus_id, OptionList).focus()

    def action_toggle(self) -> None:
        if not self._on_hosts_tab():
            return
        option_id = self._highlighted_id()
        if option_id is None:
            return
        if option_id.startswith("group:"):
            name = option_id.removeprefix("group:")
            key = f"group:{name}"
            if key in self.collapsed:
                self.collapsed.discard(key)
            else:
                self.collapsed.add(key)
        elif option_id.startswith("host:"):
            key = option_id
            if key in self.expanded:
                self.expanded.discard(key)
            else:
                self.expanded.add(key)
        self.render_list()

    @on(OptionList.OptionSelected, "#hosts")
    def on_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option.id or ""
        if option_id.startswith("group:"):
            self.action_toggle()
            return
        entry = self._entry_for(option_id)
        if entry is not None:
            self.connect(entry.alias)

    def connect(self, alias: str) -> None:
        with self.suspend():
            subprocess.run(["ssh", alias])

    def action_edit(self) -> None:
        if not self._on_hosts_tab():
            return
        entry = self._entry_for(self._highlighted_id())
        if entry is None:
            self.notify("Highlight a host first.", severity="warning")
            return
        self.push_screen(EditScreen(entry), lambda result: self._edited(entry, result))

    def _edited(self, entry: HostEntry, result: dict | None) -> None:
        if result is None:
            return
        old_block = entry.block
        new_block = sshconfig.build_block(old_block, result["alias"], result["values"])
        new_config = SshConfig(
            [new_block if block is old_block else block for block in self.config.blocks]
        )
        new_text = new_config.render()
        self._confirm_and_write(new_text, result["alias"])

    def _confirm_and_write(self, new_text: str, alias: str) -> None:
        # Overwriting an existing file is the destructive action; a new file is not.
        if self.mode == warning_text.SAFE_MODE and self.config_path.exists():
            target = sshconfig.next_backup_path(paths.backup_dir())
            self.push_screen(
                ShadowBackupScreen(self.config_path, target.name),
                lambda ok: self._write(new_text, alias, target) if ok else None,
            )
        else:
            self._write(new_text, alias)

    def _write(self, new_text: str, alias: str, target: Path | None = None) -> None:
        current = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else ""
        if current != self.file_text:
            self.notify("The config changed on disk. Reloaded it; nothing was written.", severity="error")
            self.load()
            return
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        backup_note = "no earlier file, so no backup"
        if self.config_path.exists():
            try:
                backup_path = sshconfig.backup(self.config_path, paths.backup_dir(), target=target)
                backup_note = f"backup {backup_path.name}"
            except FileExistsError:
                # The planned name was taken; use a fresh one and say so.
                backup_path = sshconfig.backup(self.config_path, paths.backup_dir())
                backup_note = f"backup {backup_path.name}, not the name shown"
        sshconfig.write_atomic(self.config_path, new_text)
        self.load()
        self.notify(f"Saved {alias} ({backup_note}).")

    def action_search(self) -> None:
        if not self._on_hosts_tab():
            return
        search = self.query_one("#search", Input)
        search.display = True
        search.focus()

    @on(Input.Changed, "#search")
    def on_search(self, event: Input.Changed) -> None:
        self.filter_text = event.value.strip()
        self.render_list()

    def action_escape(self) -> None:
        search = self.query_one("#search", Input)
        if search.display:
            search.value = ""
            search.display = False
            self.filter_text = ""
            self.render_list()
            self.query_one("#hosts", OptionList).focus()
            return
        self.exit()

    def action_reload(self) -> None:
        self.load()
        self.notify("Reloaded.")


def _mode_class(mode: str) -> str:
    return "mode-blame" if mode == warning_text.DONT_BLAME else "mode-safe"


def help_text() -> str:
    """The help box: the key menu in three columns."""
    width = max(len(item) for item in HELP_ITEMS) + 3
    rows = []
    for start in range(0, len(HELP_ITEMS), 3):
        rows.append("".join(item.ljust(width) for item in HELP_ITEMS[start:start + 3]).rstrip())
    return "\n".join(rows)


def _fuzzy(query: str, entry: HostEntry) -> bool:
    """Every character of the query appears in order in the alias or HostName."""
    haystack = f"{entry.alias} {entry.hostname}".lower()
    pattern = ".*".join(re.escape(char) for char in query.lower())
    return re.search(pattern, haystack) is not None


def _has(option_list: OptionList, option_id: str) -> bool:
    try:
        option_list.get_option_index(option_id)
    except OptionDoesNotExist:
        return False
    return True
