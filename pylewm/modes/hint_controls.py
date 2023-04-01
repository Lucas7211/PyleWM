import pylewm.modes.overlay_mode
import pylewm.modes.hint_helpers
import pylewm.commands
import pylewm
from pylewm.rects import Rect

import pywinauto
import pywinauto.uia_defines

class HintControl:
    pass

class HintControlsMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hintkeys, hotkeys, clickmode):
        self.window = pylewm.focus.FocusWindow
        self.cover_area = self.window.real_position

        self.hintkeys = hintkeys

        self.line_color = (128, 128, 255)
        self.hint_color = (255, 255, 0)
        self.center_color = (255, 0, 128)

        self.closed = False
        self.has_controls = False
        self.selection_text = ""
        self.clickmode = clickmode

        self.controls = []

        pylewm.commands.AsyncCommandThreadPool.submit(self.thread_find_controls)
        self.overlay_window(self.window)

        super(HintControlsMode, self).__init__(hotkeys)

    def thread_find_controls(self):
        uia_desktop = pywinauto.Desktop(backend="uia", allow_magic_lookup=False)
        uia_window = uia_desktop.window(handle=self.window.proxy._hwnd)
        uia_wrapper = uia_window.wrapper_object()

        def add_control(control):
            control_rect = control.rectangle()

            hint = HintControl()
            hint.rect = Rect.from_pos_size(
                (control_rect.left - self.cover_area.left, control_rect.top - self.cover_area.top),
                (control_rect.right - control_rect.left, control_rect.bottom - control_rect.top)
            )
            if hint.rect.width == 0 or hint.rect.height == 0:
                return
            if hint.rect.height < 20:
                hint.rect.bottom += 20 - hint.rect.height

            hint.control = control
            self.controls.append(hint)

        def is_control_interactable(control):
            control_class = control.friendly_class_name()
            if control_class == "Edit":
                if not control.is_editable():
                    return False
            return True

        iuia = pywinauto.uia_defines.IUIA()

        condition_list = []
        for type_name in ("Button", "TabItem", "MenuItem", "Edit", "ListItem", "TreeItem", "SplitButton", "CheckBox", "ComboBox", "Hyperlink"):
            condition_list.append(iuia.iuia.CreatePropertyCondition(
                iuia.UIA_dll.UIA_ControlTypePropertyId,
                iuia.known_control_types[type_name]
            ))
        condition = iuia.iuia.CreateOrConditionFromArray(condition_list)

        scope = iuia.tree_scope["descendants"]
        cache_enable = True

        children = uia_wrapper._element_info._get_elements(scope, condition, cache_enable)
        for element in children:
            control = uia_wrapper.backend.generic_wrapper_class(element)
            if is_control_interactable(control):
                add_control(control)

        pylewm.modes.hint_helpers.create_hints(self.controls, self.hintkeys)
        self.has_controls = True

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def update_selection(self):
        any_hints = False
        for control in self.controls:
            if control.hint == self.selection_text:
                self.confirm_selection(control)
                break
            elif control.hint.startswith(self.selection_text):
                any_hints = True
        if not any_hints:
            self.selection_text = ""

    def confirm_selection(self, control):
        self.close()

        if self.clickmode == "left":
            try:
                control.control.invoke()
            except:
                control.control.click_input()
        elif self.clickmode == "right":
            control.control.click_input(button = "right")
        elif self.clickmode == "double":
            control.control.click_input(button = "left", double=True)
        elif self.clickmode == "middle":
            control.control.click_input(button = "middle")

    def handle_key(self, key, isMod):
        if self.closed:
            return None
        if not isMod and key.down and self.has_controls:
            if len(key.key) == 1 and not key.alt.isSet and not key.app.isSet and not key.ctrl.isSet and not key.win.isSet:
                self.selection_text += key.key
                self.update_selection()
                return True
            elif key.key == 'backspace' and len(self.selection_text) >= 1:
                self.selection_text = self.selection_text[:-1]
                self.update_selection()
                return True

        return super(HintControlsMode, self).handle_key(key, isMod)

    def draw(self, overlay):
        if self.closed:
            return

        if not self.has_controls:
            overlay.draw_text("...", self.hint_color,
                Rect((0, 0, self.cover_area.width, self.cover_area.height)),
                (0.5, 0.5), font=overlay.font_small, background_box=(0,0,0))
            return
        elif not self.controls:
            overlay.draw_text("No Controls Found", self.hint_color,
                Rect((0, 0, self.cover_area.width, self.cover_area.height)),
                (0.5, 0.5), font=overlay.font_small, background_box=(0,0,0))
            return

        for i, control in enumerate(self.controls):
            if not control.hint.startswith(self.selection_text):
                continue

            overlay.draw_text(control.hint, self.hint_color,
                control.rect.shifted((0, -2)),
                (0.0, 0.0), font=overlay.font_small, background_box=(0,0,0))

@pylewm.commands.PyleCommand
def start_hint_controls(hotkeys={}, hintkeys="abcdefghijklmnopqrstuvxyz", clickmode="left"):
    """ Create hints for all controls detected through windows UI automation. """
    if not pylewm.focus.FocusWindow:
        return
    HintControlsMode(hintkeys, hotkeys, clickmode)()