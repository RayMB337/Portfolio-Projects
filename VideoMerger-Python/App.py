"""
app.py — Video Merger Boilerplate
Python 3.14+ · Textual 8.x · ffmpeg required

CHECKLIST (follow top-to-bottom):
  [ ] 1. Install deps:  pip install textual
  [ ] 2. Install ffmpeg (winget install ffmpeg  OR  choco install ffmpeg)
  [ ] 3. Verify:  ffmpeg -version  &&  ffprobe -version
  [ ] 4. Put app.py + video_merger.tcss in the same folder
  [ ] 5. Run:  python app.py
  [ ] 6. Browse left panel → select a video → Add to Queue
  [ ] 7. Add at least 2 videos, then press Merge
  [ ] 8. Find your merged output at the path shown in the Output bar
"""

from __future__ import annotations

# ─── Standard library ────────────────────────────────────────────
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

# ─── Textual ─────────────────────────────────────────────────────
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    ProgressBar,
    RichLog,
    Static,
)

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# Writes to file so you can debug without cluttering the TUI.
# ═══════════════════════════════════════════════════════════════════
logging.basicConfig(
    filename="video_merger.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("VideoMerger")

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# Add / remove extensions here to control what shows in the browser.
# ═══════════════════════════════════════════════════════════════════
VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".ts"}
)


# ═══════════════════════════════════════════════════════════════════
# CUSTOM WIDGET — VideoTree
# Subclass DirectoryTree to filter out non-video files.
# ═══════════════════════════════════════════════════════════════════
class VideoTree(DirectoryTree):
    """Directory browser that only shows folders and video files."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        # TODO: add any extra extensions you need here
        return [
            p for p in paths
            if p.is_dir() or p.suffix.lower() in VIDEO_EXTENSIONS
        ]


# ═══════════════════════════════════════════════════════════════════
# MODAL — HelpScreen
# Push this screen with self.push_screen(HelpScreen()).
# Dismiss with Escape or the Close button.
# ═══════════════════════════════════════════════════════════════════
class HelpScreen(ModalScreen):
    """Shows keyboard shortcuts. Dismissed with Esc."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        # TODO: update the help text as you add features
        with Vertical(id="help-box"):
            yield Label("Help", id="help-title")
            yield Static(
                "[b]a[/b] Add  [b]r[/b] Remove  [b]c[/b] Clear  "
                "[b]m[/b] Merge  [b]?[/b] Help  [b]q[/b] Quit",
                id="help-body",
            )
            yield Button("Close", id="help-close", variant="primary")

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.dismiss()


# ═══════════════════════════════════════════════════════════════════
# MODAL — OutputPickerScreen
# Returns a Path (the chosen folder) or None if cancelled.
# Usage:  self.push_screen(OutputPickerScreen(current), callback)
# ═══════════════════════════════════════════════════════════════════
class OutputPickerScreen(ModalScreen):
    """Folder picker modal. Returns chosen Path or None."""

    BINDINGS = [Binding("escape", "dismiss_none", "Cancel")]

    def __init__(self, current: Path) -> None:
        super().__init__()
        self._chosen: Path = current.parent   # track last clicked dir

    def compose(self) -> ComposeResult:
        # TODO: start path can be changed to a project-specific folder
        with Vertical(id="picker-box"):
            yield Label("Choose Output Folder", id="picker-title")
            yield DirectoryTree(str(Path.home()), id="picker-tree")
            yield Label(f"Selected: {self._chosen}", id="picker-selected")
            with Horizontal(id="picker-buttons"):
                yield Button("Confirm", id="picker-confirm", variant="primary")
                yield Button("Cancel",  id="picker-cancel",  variant="error")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        # Update label as user clicks folders
        self._chosen = event.path
        self.query_one("#picker-selected", Label).update(
            f"Selected: {self._chosen}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "picker-confirm":
            self.dismiss(self._chosen)
        else:
            self.dismiss(None)

    def action_dismiss_none(self) -> None:
        self.dismiss(None)


# ═══════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════
class VideoMergerApp(App):
    """Merge local video files into one MP4 using ffmpeg."""

    # Points to the .tcss file in the same directory as this script.
    CSS_PATH = "video_merger.tcss"

    TITLE    = "Video Merger"
    BINDINGS = [
        Binding("a", "add_file",    "Add"),
        Binding("r", "remove_file", "Remove"),
        Binding("c", "clear_queue", "Clear"),
        Binding("m", "merge",       "Merge"),
        Binding("?", "help",        "Help"),
        Binding("q", "quit",        "Quit"),
    ]

    # ── State ──────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()
        self._queue:        list[Path] = []          # ordered merge list
        self._selection:    Path | None = None       # highlighted in browser
        self._queue_index:  int = 0                  # highlighted in ListView
        self._output_path:  Path = Path.home() / "merged_output.mp4"
        self._merging:      bool = False

    # ── Layout ─────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header()

        # ── Main two-column area ───────────────────────────────────
        with Horizontal(id="main-layout"):

            # LEFT: file browser
            with Vertical(id="browser-panel"):
                yield Label("File Browser", id="browser-title")
                yield VideoTree(str(Path.home()), id="video-tree")

            # RIGHT: everything else
            with Vertical(id="right-panel"):

                # Queue list
                with Vertical(id="queue-panel"):
                    yield Label("Merge Queue", id="queue-title")
                    yield ListView(id="queue-list")
                    yield Label(
                        "No videos yet — browse left and press Add",
                        id="queue-empty",
                    )

                # Buttons
                # TODO: add more buttons here (e.g. Preview, Settings)
                with Horizontal(id="controls"):
                    yield Button("Add",    id="btn-add",    variant="success",  disabled=True)
                    yield Button("Remove", id="btn-remove", variant="warning",  disabled=True)
                    yield Button("Clear",  id="btn-clear",  variant="error",    disabled=True)
                    yield Button("Up",     id="btn-up",                         disabled=True)
                    yield Button("Down",   id="btn-down",                       disabled=True)
                    yield Button("Output", id="btn-output")
                    yield Button("Merge",  id="btn-merge",  variant="primary",  disabled=True)
                    yield Button("Help",   id="btn-help")

                # Output path display
                with Horizontal(id="output-bar"):
                    yield Label("Output:", id="output-label")
                    yield Label(str(self._output_path), id="output-path")

                # Progress (0–100)
                yield ProgressBar(id="progress-bar", total=100, show_eta=False)

                # Activity log panel
                with Vertical(id="log-panel"):
                    yield Label("Log", id="log-title")
                    yield RichLog(id="rich-log", highlight=True, markup=True)

        yield Footer()

    # ── Mount ──────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._log("App ready. Select a video in the browser, then press [b]Add[/b].")
        self._refresh_queue()

    # ── Helpers ────────────────────────────────────────────────────
    def _log(self, msg: str) -> None:
        """Write to on-screen RichLog and the log file."""
        try:
            self.query_one("#rich-log", RichLog).write(msg)
        except Exception:
            pass
        log.info(re.sub(r"\[.*?\]", "", msg))   # strip markup for file

    def _refresh_queue(self, focus: int = 0) -> None:
        """Rebuild the ListView from self._queue and sync button states."""
        lv    = self.query_one("#queue-list",  ListView)
        empty = self.query_one("#queue-empty", Label)

        lv.clear()
        if not self._queue:
            empty.display = True
        else:
            empty.display = False
            for i, p in enumerate(self._queue):
                lv.append(ListItem(Label(f"[b]{i+1:02}.[/b] {p.name}")))

        has  = bool(self._queue)
        many = len(self._queue) >= 2
        idx  = self._queue_index
        n    = len(self._queue)

        # Enable/disable buttons based on state
        self.query_one("#btn-remove", Button).disabled = not has  or self._merging
        self.query_one("#btn-clear",  Button).disabled = not has  or self._merging
        self.query_one("#btn-merge",  Button).disabled = not many or self._merging
        self.query_one("#btn-up",     Button).disabled = n < 2 or idx == 0     or self._merging
        self.query_one("#btn-down",   Button).disabled = n < 2 or idx >= n - 1 or self._merging

    def _set_merging(self, state: bool) -> None:
        self._merging = state
        self._refresh_queue()
        self.query_one("#btn-output", Button).disabled = state
        self.query_one("#btn-help",   Button).disabled = state

    # ── Browser events ─────────────────────────────────────────────
    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        if event.path.suffix.lower() not in VIDEO_EXTENSIONS:
            self._log(f"[yellow]Not a video:[/yellow] {event.path.name}")
            self._selection = None
            self.query_one("#btn-add", Button).disabled = True
            return
        self._selection = event.path
        self._log(f"[cyan]Selected:[/cyan] {event.path.name}")
        self.query_one("#btn-add", Button).disabled = False

    def on_directory_tree_directory_selected(self, _: DirectoryTree.DirectorySelected) -> None:
        self._selection = None
        self.query_one("#btn-add", Button).disabled = True

    # ── Queue events ───────────────────────────────────────────────
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        lv = self.query_one("#queue-list", ListView)
        self._queue_index = lv.index or 0
        self._refresh_queue()

    # ── Button dispatcher ──────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-add":    self.action_add_file,
            "btn-remove": self.action_remove_file,
            "btn-clear":  self.action_clear_queue,
            "btn-up":     self.action_move_up,
            "btn-down":   self.action_move_down,
            "btn-merge":  self.action_merge,
            "btn-output": self.action_pick_output,
            "btn-help":   self.action_help,
        }
        fn = actions.get(event.button.id or "")
        if fn:
            fn()

    # ── Actions ────────────────────────────────────────────────────
    def action_add_file(self) -> None:
        if not self._selection:
            return
        if self._selection in self._queue:
            self._log(f"[yellow]Already queued:[/yellow] {self._selection.name}")
            return
        self._queue.append(self._selection)
        self._log(f"[green]Added:[/green] {self._selection.name}")
        self._refresh_queue()

    def action_remove_file(self) -> None:
        if not self._queue:
            return
        removed = self._queue.pop(self._queue_index)
        self._log(f"[red]Removed:[/red] {removed.name}")
        self._queue_index = max(0, self._queue_index - 1)
        self._refresh_queue()

    def action_clear_queue(self) -> None:
        if not self._queue:
            return
        self._queue.clear()
        self._log("[red]Queue cleared.[/red]")
        self._refresh_queue()

    def action_move_up(self) -> None:
        i = self._queue_index
        if i > 0:
            self._queue[i], self._queue[i - 1] = self._queue[i - 1], self._queue[i]
            self._queue_index -= 1
            self._refresh_queue()

    def action_move_down(self) -> None:
        i = self._queue_index
        if i < len(self._queue) - 1:
            self._queue[i], self._queue[i + 1] = self._queue[i + 1], self._queue[i]
            self._queue_index += 1
            self._refresh_queue()

    def action_pick_output(self) -> None:
        self.push_screen(OutputPickerScreen(self._output_path), self._on_output_picked)

    def _on_output_picked(self, folder: Path | None) -> None:
        if folder is None:
            return
        self._output_path = folder / self._output_path.name
        self.query_one("#output-path", Label).update(str(self._output_path))
        self._log(f"[green]Output set:[/green] {self._output_path}")

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_merge(self) -> None:
        if self._merging or len(self._queue) < 2:
            return
        self._run_merge()

    # ── Merge worker (runs in background thread) ───────────────────
    @work(exclusive=True, thread=True)
    def _run_merge(self) -> None:
        """
        Background thread: writes a concat list then calls ffmpeg.

        TODO: add re-encode options, resolution normalisation, or
              subtitle/chapter injection here before the ffmpeg call.
        """
        self.call_from_thread(self._set_merging, True)

        # Step 1 — probe total duration for accurate progress bar
        total_s = self._probe_duration()
        self.call_from_thread(self._log, f"Total duration: {total_s:.1f}s")

        with tempfile.TemporaryDirectory() as tmp:
            concat = Path(tmp) / "list.txt"

            # Step 2 — write concat demuxer file
            try:
                lines = "\n".join(
                    f"file '{str(p).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'"
                    for p in self._queue
                )
                concat.write_text(lines, encoding="utf-8")
            except OSError as exc:
                self.call_from_thread(self._on_error, str(exc))
                return

            # Step 3 — build ffmpeg command
            # TODO: change -crf (18=high quality, 28=smaller file)
            # TODO: change -preset (ultrafast → veryslow) for speed vs size
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(self._output_path),
            ]
            log.debug("ffmpeg cmd: %s", " ".join(cmd))

            # Step 4 — run and parse progress from stderr
            try:
                proc = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except FileNotFoundError:
                self.call_from_thread(
                    self._on_error,
                    "ffmpeg not found — is it installed and on PATH?",
                )
                return

            assert proc.stderr
            for line in proc.stderr:
                line = line.strip()
                if not line:
                    continue
                log.debug("[ffmpeg] %s", line)
                # Parse  time=HH:MM:SS.ss  for progress
                m = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                if m and total_s > 0:
                    elapsed = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                    pct = min(int(elapsed / total_s * 100), 99)
                    self.call_from_thread(
                        self.query_one("#progress-bar", ProgressBar).update,
                        progress=pct,
                    )

            proc.wait()

        if proc.returncode == 0:
            self.call_from_thread(self._on_success)
        else:
            self.call_from_thread(self._on_error, f"ffmpeg exited {proc.returncode}")

    def _probe_duration(self) -> float:
        """Sum durations of all queued files with ffprobe."""
        total = 0.0
        for p in self._queue:
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "error",
                     "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1",
                     str(p)],
                    capture_output=True, text=True, timeout=10,
                )
                total += float(r.stdout.strip())
            except Exception:
                pass
        return total

    def _on_success(self) -> None:
        self.query_one("#progress-bar", ProgressBar).update(progress=100)
        self._log(f"[b green]Merge complete:[/b green] {self._output_path}")
        self.notify("Done!", title="Merge complete", severity="information")
        self._set_merging(False)

    def _on_error(self, msg: str) -> None:
        self._log(f"[b red]Error:[/b red] {msg}")
        self.notify(msg, title="Error", severity="error")
        self.query_one("#progress-bar", ProgressBar).update(progress=0)
        self._set_merging(False)


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def main() -> None:
    missing = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    if missing:
        print(f"\nMissing: {', '.join(missing)}")
        print("Install ffmpeg:  winget install Gyan.FFmpeg")
        raise SystemExit(1)

    VideoMergerApp().run()


if __name__ == "__main__":
    main()
