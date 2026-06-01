# Template Manager — a Glyphs.app plugin

Capture the *structure* of an existing font — glyph set, kerning groups, kerning
values, masters & metrics — as a reusable, **outline-free** `.glyphs` template,
then spin up new untitled documents from it. Start every project with your base
character set and pre-wired kerning groups already in place.

Adds **Edit → Template Manager…** to Glyphs.

---

## Install (testers)

This installs through the **Plugin Manager**, which also installs the required
modules (Vanilla, Python) automatically.

1. In Glyphs: **Settings → Addons → Alternate Plugin Repos** → click **+** and
   paste this, then OK:
   ```
   https://raw.githubusercontent.com/telemetry/GlyphsTemplateManager/main/packages.plist
   ```
2. Go to **Window → Plugin Manager → Plugins**, find **Template Manager**, click
   **Install**. If it offers to also install **Vanilla**, accept.
3. **Quit Glyphs (⌘Q) and reopen it.**
4. Open a font, then go to **Edit → Template Manager…**

If the menu item doesn't appear, open **Window → Macro Panel** and run
`import objc, vanilla; print(objc.__version__)` — a version number means the
Python bridge is ready; an error means the modules didn't install (reinstall via
Plugin Manager → Modules and pick a **Python Version** under Settings → Addons).

Tested on Glyphs 3.4.1 (build 3436), Python 3.11.

---

## Install from source (development)

```sh
./install.sh        # copies the bundle into your Glyphs Plugins folder
```

Then relaunch Glyphs. (A plain copy is used rather than a symlink because macOS
privacy protection blocks Glyphs from following symlinks into Desktop/Documents.)

---

## Use

1. Open a font you want to template.
2. **Edit → Template Manager…**
3. **Save Current Font as Template…** — stores an outline-free copy (keeps glyph
   set, kerning groups, kerning, masters and metrics).
4. **New Document from Selected Template** — opens a fresh untitled font with the
   same glyphs (empty) and all your kerning groups already wired up.

Templates are stored in `~/Library/Application Support/Glyphs 3/Templates/`.

---

## Development

Glyphs loads plugins only at launch, so the edit loop is:

```sh
# edit Contents/Resources/plugin.py
./install.sh        # re-copy into Plugins
# ⌘Q Glyphs, relaunch
```

Errors surface in **Window → Macro Panel** at launch. The plugin logs failures
to the system log tagged `TemplateManager:`.
