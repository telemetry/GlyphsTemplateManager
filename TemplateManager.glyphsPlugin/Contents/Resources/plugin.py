# encoding: utf-8

###########################################################################################################
#
#   Template Manager — General Plugin for Glyphs.app
#
#   Capture the *structure* of the current font (glyph set, kerning groups,
#   kerning values, masters & metrics) as a reusable, outline-free .glyphs
#   template, and spin up new untitled documents from it.
#
###########################################################################################################

from __future__ import print_function, unicode_literals

import os
import re
import traceback

import objc
from Foundation import NSLog, NSBundle, NSURL, NSMakeRect
from AppKit import NSMenuItem, NSAlert, NSTextField, NSWorkspace
from GlyphsApp import Glyphs, EDIT_MENU, Message
from GlyphsApp.plugins import GeneralPlugin

NS_ALERT_FIRST_BUTTON = 1000  # NSAlertFirstButtonReturn

try:
    import vanilla
    HAS_VANILLA = True
except Exception:
    NSLog("TemplateManager: vanilla not available\n" + traceback.format_exc())
    HAS_VANILLA = False


# ----------------------------------------------------------------------------- helpers

def templates_dir():
    """Templates folder next to the Plugins folder, created on demand.

    Derives the app's support folder from the running app's bundle name.
    """
    app_name = os.path.splitext(os.path.basename(NSBundle.mainBundle().bundlePath()))[0]
    path = os.path.expanduser("~/Library/Application Support/%s/Templates" % app_name)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def template_names():
    names = []
    for entry in sorted(os.listdir(templates_dir())):
        if entry.endswith(".glyphs"):
            names.append(entry[:-len(".glyphs")])
    return names


def sanitize_name(name):
    name = (name or "").strip()
    name = re.sub(r'[/\\:*?"<>|]', "_", name)
    return name or "Template"


def ask_text(message, default=""):
    """Modal single-field prompt. Returns the string, or None if cancelled."""
    alert = NSAlert.alloc().init()
    alert.setMessageText_(message)
    alert.addButtonWithTitle_("OK")
    alert.addButtonWithTitle_("Cancel")
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 24))
    field.setStringValue_(default)
    alert.setAccessoryView_(field)
    alert.window().setInitialFirstResponder_(field)
    if alert.runModal() == NS_ALERT_FIRST_BUTTON:
        return field.stringValue()
    return None


def ask_yes_no(message, info=""):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(message)
    if info:
        alert.setInformativeText_(info)
    alert.addButtonWithTitle_("OK")
    alert.addButtonWithTitle_("Cancel")
    return alert.runModal() == NS_ALERT_FIRST_BUTTON


def strip_outlines(font):
    """Empty every layer's drawing while keeping glyph entries, unicodes,
    kerning groups, kerning, masters, metrics and custom parameters intact."""
    for glyph in font.glyphs:
        for layer in glyph.layers:
            layer.shapes = []   # paths + components (unified container in Glyphs 3)
            layer.anchors = []
            layer.hints = []
    return font


# ----------------------------------------------------------------------------- window

class TemplateManagerWindow(object):

    def __init__(self):
        self.w = vanilla.Window((360, 380), "Templates", minSize=(300, 260))
        self.w.list = vanilla.List(
            (10, 10, -10, -96),
            template_names(),
            allowsMultipleSelection=False,
            doubleClickCallback=self.new_from_template,
        )
        self.w.newButton = vanilla.Button(
            (10, -88, -10, 22), "New Document from Selected Template",
            callback=self.new_from_template,
        )
        self.w.saveButton = vanilla.Button(
            (10, -60, -10, 22), "Save Current Font as Template…",
            callback=self.save_current,
        )
        self.w.deleteButton = vanilla.Button(
            (10, -32, 168, 22), "Delete", callback=self.delete_selected,
        )
        self.w.revealButton = vanilla.Button(
            (-178, -32, 168, 22), "Reveal in Finder", callback=self.reveal_selected,
        )
        self.w.open()

    # -- data
    @objc.python_method
    def refresh(self, select=None):
        names = template_names()
        self.w.list.set(names)
        if select and select in names:
            self.w.list.setSelection([names.index(select)])

    @objc.python_method
    def selected_name(self):
        sel = self.w.list.getSelection()
        if not sel:
            return None
        return self.w.list[sel[0]]

    # -- actions
    def save_current(self, sender=None):
        font = Glyphs.font
        if font is None:
            Message("No font open", "Open a font, then save it as a template.")
            return
        default = font.familyName or "Template"
        raw = ask_text("Save current font as template named:", default)
        if raw is None:
            return
        name = sanitize_name(raw)
        path = os.path.join(templates_dir(), name + ".glyphs")
        if os.path.exists(path):
            if not ask_yes_no("Replace template “%s”?" % name,
                              "A template with this name already exists."):
                return
        try:
            template = font.copy()
            strip_outlines(template)
            template.save(path)
        except Exception as e:
            NSLog("TemplateManager save error:\n" + traceback.format_exc())
            Message("Could not save template", str(e))
            return
        self.refresh(select=name)

    def new_from_template(self, sender=None):
        name = self.selected_name()
        if not name:
            Message("No template selected", "Select a template from the list first.")
            return
        path = os.path.join(templates_dir(), name + ".glyphs")
        if not os.path.exists(path):
            Message("Template missing", "The file for “%s” was not found." % name)
            self.refresh()
            return
        try:
            opened = Glyphs.open(path, showInterface=False)
            if opened is None:
                Message("Could not open template", path)
                return
            new_font = opened.copy()
            # Close the read-only source doc (untouched, so no save prompt),
            # then open the copy as a fresh untitled document.
            parent = getattr(opened, "parent", None)
            if parent is not None:
                parent.close()
            Glyphs.fonts.append(new_font)
        except Exception as e:
            NSLog("TemplateManager new-from-template error:\n" + traceback.format_exc())
            Message("Could not create document", str(e))

    def delete_selected(self, sender=None):
        name = self.selected_name()
        if not name:
            return
        if not ask_yes_no("Delete template “%s”?" % name,
                          "This removes the template file. It cannot be undone."):
            return
        try:
            os.remove(os.path.join(templates_dir(), name + ".glyphs"))
        except OSError as e:
            Message("Could not delete", str(e))
        self.refresh()

    def reveal_selected(self, sender=None):
        name = self.selected_name()
        target = os.path.join(templates_dir(), name + ".glyphs") if name else templates_dir()
        NSWorkspace.sharedWorkspace().activateFileViewerSelectingURLs_(
            [NSURL.fileURLWithPath_(target)]
        )


# ----------------------------------------------------------------------------- plugin

class TemplateManagerPlugin(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = "Template Manager…"
        self.window = None

    @objc.python_method
    def start(self):
        try:
            if Glyphs.buildNumber >= 3320:
                from GlyphsApp.UI import MenuItem
                item = MenuItem(self.name, action=self.showWindow_, target=self)
            else:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    self.name, self.showWindow_, "")
                item.setTarget_(self)
            Glyphs.menu[EDIT_MENU].append(item)
        except Exception:
            NSLog("TemplateManager menu error:\n" + traceback.format_exc())

    def showWindow_(self, sender):
        if not HAS_VANILLA:
            Message("Missing module",
                    "Template Manager needs the 'vanilla' module. Install it via "
                    "Window > Plugin Manager > Modules.")
            return
        if self.window is None or getattr(self.window.w, "_window", None) is None:
            self.window = TemplateManagerWindow()
        else:
            self.window.w.show()

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
