import fnmatch

def matches(window, sel):
    if isinstance(sel, list) or isinstance(sel, tuple):
        for s in sel:
            if matches(window, s):
                return True
        return False
    elif isinstance(sel, dict):
        if "class" in sel:
            if not fnmatch.fnmatch(window.window_class.lower(), sel["class"].lower()):
                return False
        if "title" in sel:
            if not fnmatch.fnmatch(window.window_title.lower(), sel["title"].lower()):
                return False
        if "child" in sel:
            if window.is_child_window != sel["child"]:
                return False
        return True
    return None
