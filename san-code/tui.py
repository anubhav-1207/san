from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import TextArea, Footer, Header, Input, Label
from textual._tree_sitter import get_language
from textual import events
from pathlib import Path

# Extra tree-sitter query rules for SAN-specific keywords
# (JS grammar parses them as identifiers, so we match by name)
SAN_EXTRAS = """
((identifier) @keyword
 (#any-of? @keyword
  "dec" "flux" "func" "skip" "stdout" "scan"
  "Null" "use" "type" "init" "ext" "drop"))
"""


class SANTextArea(TextArea):
    # --- Auto-indent and braces completion ---------------------------------
    async def _on_key(self, event: events.Key) -> None:
        if not self.read_only:
            # "{" and insert "{}"" and place cursor between
            if event.character == "{":
                event.stop()
                event.prevent_default()
                s, e = self.selection
                self._replace_via_keyboard("{}", s, e)
                self.move_cursor((s[0], s[1] + 1))
                return
            # smart indent (may be broken.)
            if event.key == "enter":
                event.stop()
                event.prevent_default()
                s, e = self.selection
                line = self.document[s[0]]
                ind = len(line) - len(line.lstrip())  # current indent level
                if line.strip() == "{}":
                    # Expand `{}` into three lines with cursor in the middle
                    self._replace_via_keyboard(
                        f"\n{' ' * (ind + self.indent_width)}\n{' ' * ind}}}",
                        (s[0], 0),
                        (s[0], len(line)),
                    )
                    self.move_cursor((s[0] + 1, ind + self.indent_width))
                elif line.strip().endswith("{"):
                    # Indent one level deeper after `{`
                    self._replace_via_keyboard(
                        f"\n{' ' * (ind + self.indent_width)}", s, e
                    )
                else:
                    # Keep same indent level
                    self._replace_via_keyboard(f"\n{' ' * ind}", s, e)
                return
        await super()._on_key(event)


class SaveScreen(Screen):
    # --- Simple dialog: ask for filename, save as .san ------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label("Save as:")
        yield Input(placeholder="filename")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if not name:
            return
        if not name.endswith(".san"):
            name += ".san"
        Path(name).write_text(self.app.query_one(SANTextArea).text)
        self.app.pop_screen()
        self.app.query_one(SANTextArea).focus()


class SANEditor(App):
    BINDINGS = [("ctrl+s", "save_file", "Save")]
    CSS = "TextArea { background: #1e1e1e; color: white; }"

    def __init__(self, initial_text="", **kwargs):
        self._initial_text = initial_text
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header()

        # Register SAN language using JS tree-sitter
        q = TextArea._get_builtin_highlight_query("javascript")
        js = get_language("javascript")
        if js is None:
            raise RuntimeError("tree-sitter-javascript not installed")

        self.editor = SANTextArea.code_editor(theme="monokai")
        self.editor.register_language("san", js, q + "\n" + SAN_EXTRAS)
        self.editor.language = "san"

        if self._initial_text:
            self.editor.text = self._initial_text

        yield self.editor
        yield Footer()

    def action_save_file(self) -> None:
        self.push_screen(SaveScreen())
