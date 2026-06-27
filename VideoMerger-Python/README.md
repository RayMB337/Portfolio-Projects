# Textual 8.x — Full Component Catalogue
> Extracted live from `textual==8.2.7`. Every widget, container, screen, valid CSS property, and theme variable.

---

## Checklist — Video Merger

```
[ ] 1. pip install textual
[ ] 2. winget install Gyan.FFmpeg  (or choco / scoop)
[ ] 3. Open a NEW terminal and run:  ffmpeg -version && ffprobe -version
[ ] 4. Place app.py and video_merger.tcss in the same folder
[ ] 5. python app.py
[ ] 6. Browse left panel → click a video → Add button (or press A)
[ ] 7. Repeat until you have 2+ videos in the queue
[ ] 8. Reorder with Up / Down if needed
[ ] 9. Click Output to choose where to save
[ ] 10. Press Merge — watch the progress bar
[ ] 11. Find merged_output.mp4 at the path shown in the Output bar
[ ] 12. Check video_merger.log if something went wrong
```

---

## Widgets — `from textual.widgets import ...`

| Widget | Key Args | What It Does |
|---|---|---|
| `Button` | `label, variant, action, compact` | Clickable button. `variant=` one of `default primary success warning error`. Fires `Button.Pressed`. |
| `Checkbox` | `label, value, button_first` | Boolean toggle. Fires `Checkbox.Changed`. |
| `Collapsible` | `title, collapsed` | Expandable/collapsible section. Child widgets shown/hidden on click. |
| `ContentSwitcher` | `initial` | Shows one child at a time. Switch with `.current = "id"`. |
| `DataTable` | `show_header, zebra_stripes, fixed_rows, fixed_columns` | Full spreadsheet-style table with sorting and cursor. |
| `Digits` | `value` | Big chunky number display using Unicode block chars. |
| `DirectoryTree` | `path` | File/folder browser. Fires `FileSelected`, `DirectorySelected`. |
| `Footer` | `show_command_palette, compact` | Bottom bar showing key bindings from `BINDINGS`. |
| `Header` | `show_clock, icon` | Top bar with app title and optional live clock. |
| `HelpPanel` | — | Context-sensitive help for the focused widget. |
| `Input` | `value, placeholder, password, restrict, type` | Single-line text input. Fires `Input.Changed`, `Input.Submitted`. |
| `KeyPanel` | — | Shows bindings for the currently focused widget. |
| `Label` | `content, variant` | Static text. Supports Rich markup. |
| `Link` | `text, url` | Clickable hyperlink that opens in browser. |
| `ListItem` | `*children` | A row inside `ListView`. |
| `ListView` | `*children, initial_index` | Vertical scrollable list. Fires `Highlighted`, `Selected`. |
| `LoadingIndicator` | — | Animated spinner. Show while waiting for async work. |
| `Log` | `highlight, max_lines, auto_scroll` | Simple text log (plain text only). |
| `Markdown` | `markdown, open_links` | Renders Markdown string. |
| `MarkdownViewer` | `markdown, show_table_of_contents` | Markdown with scrollable ToC panel. |
| `MaskedInput` | `template, value, placeholder` | Input with a format mask (e.g. phone, date). |
| `OptionList` | `*content, compact` | Scrollable option picker. Fires `OptionSelected`. |
| `Placeholder` | `label, variant` | Dev placeholder — shows widget bounds. |
| `Pretty` | `object` | Pretty-prints any Python object using Rich. |
| `ProgressBar` | `total, show_bar, show_percentage, show_eta` | Progress bar. Call `.update(progress=n)` or `.advance(n)`. |
| `RadioButton` | `label, value` | Single radio button. Best used inside `RadioSet`. |
| `RadioSet` | `*buttons` | Group of radio buttons — only one active at a time. |
| `RichLog` | `max_lines, wrap, highlight, markup, auto_scroll` | Log panel for Rich renderables. Call `.write(text)`. |
| `Rule` | `orientation, line_style` | Horizontal or vertical divider line. |
| `Select` | `options, prompt, allow_blank, value` | Dropdown selector. Fires `Select.Changed`. |
| `SelectionList` | `*selections, compact` | Multi-select checklist. Fires `SelectionList.SelectedChanged`. |
| `Sparkline` | `data, min_color, max_color, summary_function` | Inline mini bar chart from a list of numbers. |
| `Static` | `content` | Read-only text / renderable display. Base class for custom widgets. |
| `Switch` | `value, animate` | On/off toggle. Fires `Switch.Changed`. |
| `Tab` | `label` | A single tab inside `Tabs`. |
| `TabbedContent` | `*titles, initial` | Tabs + content panes in one widget. Use with `TabPane`. |
| `TabPane` | `title, *children` | Content pane for `TabbedContent`. |
| `Tabs` | `*tabs, active` | Row of tabs only (no content). Fires `Tabs.TabActivated`. |
| `TextArea` | `text, language, theme, soft_wrap, tab_behavior` | Multi-line code/text editor with syntax highlighting. |
| `Tooltip` | `content` | Hover tooltip attached to any widget via `.tooltip = "..."`. |
| `Tree` | `label, data` | Generic collapsible tree. Fires `Tree.NodeSelected`. |
| `Welcome` | — | Built-in Textual welcome/splash screen. |

---

## Containers — `from textual.containers import ...`

| Container | Layout | Scrolls? | Use For |
|---|---|---|---|
| `Container` | vertical | no | Generic wrapper — add `layout:` in CSS |
| `Vertical` | vertical | no | Stack children top-to-bottom |
| `Horizontal` | horizontal | no | Stack children left-to-right |
| `VerticalScroll` | vertical | Y axis | Scrollable vertical stack |
| `HorizontalScroll` | horizontal | X axis | Scrollable horizontal stack |
| `ScrollableContainer` | vertical | both axes | Scroll in any direction |
| `VerticalGroup` | vertical | no | Non-expanding vertical (wraps content height) |
| `HorizontalGroup` | horizontal | no | Non-expanding horizontal (wraps content width) |
| `Grid` | grid | no | Manual grid — set `grid-size` in CSS |
| `ItemGrid` | grid | no | Auto-columns grid (wraps items) |
| `Center` | — | no | Centers children on X axis |
| `Middle` | — | no | Centers children on Y axis |
| `Right` | — | no | Right-aligns children on X axis |
| `CenterMiddle` | — | no | Centers children on both axes — great for modals |

---

## Screens — `from textual.screen import ...`

| Screen | Use For |
|---|---|
| `Screen` | Main full-screen view. Push/pop via `app.push_screen()`. |
| `ModalScreen` | Floating overlay. Bindings take priority. Dismiss with `self.dismiss(value)`. |
| `SystemModalScreen` | Internal Textual use (command palette etc). Avoid subclassing. |

---

## Valid CSS Properties (Textual 8.x)

These are the **only** properties accepted in `.tcss` files.  
Anything else causes a CSS parse error at startup.

```
Layout & Size
  layout               horizontal | vertical | grid
  width                1fr | 50% | 20 | auto
  height               1fr | 50% | 20 | auto
  min-width            scalar
  min-height           scalar
  max-width            scalar
  max-height           scalar

Spacing
  margin               1 | 1 2 | 1 2 3 4   (top right bottom left)
  margin-top           scalar
  margin-right         scalar
  margin-bottom        scalar
  margin-left          scalar
  padding              1 | 1 2 | 1 2 3 4
  padding-top          scalar
  padding-right        scalar
  padding-bottom       scalar
  padding-left         scalar

Colour & Style
  background           $primary | red | #ff0000 | rgb(255,0,0)
  background-tint      color (blended over background)
  color                foreground text color
  opacity              0.0 – 1.0
  text-opacity         0.0 – 1.0
  tint                 color (tints the whole widget)

Text
  text-style           bold | italic | underline | strike | dim | combinations
  text-align           left | center | right
  text-overflow        fold | ellipsis | clip
  text-wrap            wrap | nowrap

Border & Outline
  border               round $primary | solid red | none | heavy | double | etc.
  border-top           same values
  border-right         same values
  border-bottom        same values
  border-left          same values
  outline              same values (drawn ON the widget, not around it)

Overflow (NO shorthand 'overflow' — use -x and -y separately)
  overflow-x           auto | hidden | scroll
  overflow-y           auto | hidden | scroll

Alignment (for children inside a container)
  align                center middle | left top | right bottom | etc.
  align-horizontal     left | center | right
  align-vertical       top | middle | bottom
  content-align        same (for widget content, not children)

Position & Layer
  dock                 top | right | bottom | left
  offset               (x, y)
  offset-x             scalar
  offset-y             scalar
  position             relative | absolute
  layer                layer-name
  layers               layer-name ...
  overlay              screen | parent

Grid (only inside a Grid container)
  grid-size            columns rows
  grid-columns         scalar ...
  grid-rows            scalar ...
  grid-gutter          horizontal vertical
  column-span          integer
  row-span             integer

Scrollbar
  scrollbar-visibility   auto | hidden | visible
  scrollbar-size         horizontal vertical
  scrollbar-gutter       stable | auto
  scrollbar-color        color
  scrollbar-background   color

Other
  display              block | none
  visibility           visible | hidden
  box-sizing           border-box | content-box
  pointer              default | not-allowed | hand | etc.
  transition           property duration easing delay
  hatch                pattern color opacity
  split                horizontal | vertical
```

**NOT valid (common mistakes):**
```
gap          ✗  →  use margin on children
variant      ✗  →  Python constructor arg only
flex-*       ✗  →  no flexbox in Textual
font-*       ✗  →  Textual uses terminal fonts
cursor       ✗  →  use pointer:
overflow     ✗  →  must be overflow-x: or overflow-y:
```

---

## Theme CSS Variables

Safe to use anywhere in `.tcss`. All support `-darken-1/2/3` and `-lighten-1/2/3` suffixes.

```
Core colours
  $primary          Brand primary colour
  $secondary        Brand secondary colour
  $accent           Highlight / accent colour
  $success          Green tones
  $warning          Amber/yellow tones
  $error            Red tones
  $background       App background
  $surface          Widget surface (slightly lighter than background)
  $panel            Panel / sidebar background
  $foreground       Default text colour
  $boost            Brightness boost overlay

Derived (auto-generated from core colours)
  $primary-darken-1   $primary-darken-2   $primary-darken-3
  $primary-lighten-1  $primary-lighten-2  $primary-lighten-3
  $primary-muted      (same for secondary, accent, success, warning, error)

Text semantic colours
  $text-muted         Dimmed / hint text
  $text-primary       Text on primary background
  $text-secondary     Text on secondary background
  $text-success       Text on success background
  $text-warning       Text on warning background
  $text-error         Text on error background
  $text-accent        Text on accent background
  $text-disabled      Greyed-out text

Block cursor (DataTable, ListView, Tree)
  $block-cursor-background
  $block-cursor-foreground
  $block-cursor-text-style
  $block-cursor-blurred-background
  $block-cursor-blurred-foreground
  $block-hover-background

Input
  $input-cursor-background
  $input-cursor-foreground
  $input-selection-background

Border
  $border             Active border colour
  $border-blurred     Unfocused border colour

Footer
  $footer-background
  $footer-foreground

Scrollbar
  $scrollbar           scrollbar thumb
  $scrollbar-hover     scrollbar thumb on hover
  $scrollbar-active    scrollbar thumb active
  $scrollbar-background
  $scrollbar-corner-color
```

---

## App Skeleton Reference

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Vertical, Horizontal

class MyApp(App):
    CSS_PATH = "styles.tcss"   # external stylesheet
    TITLE    = "My App"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Hello")
            yield Button("Click me", id="my-btn", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "my-btn":
            self.notify("Button pressed!")

    def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    MyApp().run()
```

---

## TCSS Skeleton Reference

```css
/* styles.tcss */

Screen {
    background: $surface;
    color: $foreground;
}

/* Containers use layout: horizontal or vertical */
#main {
    layout: horizontal;
    height: 1fr;
    margin: 1 2;
}

/* Sizing: fr = fractional unit, % = percent of parent, int = cells */
#sidebar {
    width: 30%;
    border: round $primary;
    padding: 1;
}

#content {
    width: 1fr;         /* takes remaining space */
    layout: vertical;
    margin-left: 1;
}

/* Spacing between children: no 'gap' — use margin on elements */
Button {
    margin-right: 1;
    margin-bottom: 1;
    min-width: 12;
}

/* Target variant classes set by variant= in Python */
Button.-primary  { background: $primary;  color: $foreground; }
Button.-success  { background: $success;  color: $foreground; }
Button.-warning  { background: $warning;  color: $foreground; }
Button.-error    { background: $error;    color: $foreground; }

/* Modal screens */
MyModal {
    align: center middle;   /* centre in the screen */
}
#modal-box {
    width: 60;
    height: auto;
    border: double $primary;
    padding: 2 3;
    background: $panel;
    layout: vertical;
}
```
