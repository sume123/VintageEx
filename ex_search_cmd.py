# TODO(guillermooo): All of this functionality, along with key bindings, rather
# belongs in Vintage, but we need to extract the necessary functions out of
# VintageEx first. This is a temporary solution.

import sublime
import sublime_plugin

import ex_location


class SearchImpl(object):
    last_term = ""
    def __init__(self, view, cmd, remember=True, start_sel=None):
        self.start_sel = start_sel
        self.remember = remember
        if not cmd:
            return
        self.view = view
        self.reversed = cmd.startswith("?")
        if not cmd.startswith(("?", "/")):
            cmd = "/" + cmd
        if len(cmd) == 1 and SearchImpl.last_term:
            cmd += SearchImpl.last_term
        elif not cmd:
            return
        self.cmd = cmd[1:]

    def search(self):
        if not getattr(self, "cmd", None):
            return
        if self.remember:
            SearchImpl.last_term = self.cmd
        sel = self.start_sel[0]

        next_match = None
        if self.reversed:
            current_line = self.view.line(self.view.sel()[0])
            left_side = sublime.Region(current_line.begin(), self.view.sel()[0].begin())
            if ex_location.search_in_range(self.view, self.cmd, left_side.begin(), left_side.end()):
                next_match = ex_location.find_last_match(self.view, self.cmd, left_side.begin(), left_side.end())
            else:
                line_nr = ex_location.reverse_search(self.view, self.cmd,
                                                end=current_line.begin() - 1)
                if line_nr:
                    pt = self.view.text_point(line_nr - 1, 0)
                    next_match = self.view.find(self.cmd, pt)
        else:
            next_match = self.view.find(self.cmd, sel.end())
        if next_match:
            self.view.sel().clear()
            if not self.remember:
                self.view.add_regions("vi_search", [next_match], "search.vi", sublime.DRAW_OUTLINED)
            else:
                self.view.sel().add(next_match)
            self.view.show(next_match)
        else:
            sublime.status_message("VintageEx: Could not find:" + self.cmd)


class ViRepeatSearchBackward(sublime_plugin.TextCommand):
   def run(self, edit):
       SearchImpl(self.view, "?" + SearchImpl.last_term, start_sel=self.view.sel()).search()


class ViRepeatSearchForward(sublime_plugin.TextCommand):
    def run(self, edit):
        SearchImpl(self.view, SearchImpl.last_term, start_sel=self.view.sel()).search()


class ViSearch(sublime_plugin.TextCommand):
    def run(self, edit, initial_text=""):
        self.original_sel = list(self.view.sel())
        self.view.window().show_input_panel("", initial_text,
                                            self.on_done,
                                            self.on_change,
                                            self.on_cancel)

    def on_done(self, s):
        self._restore_sel()
        SearchImpl(self.view, s, start_sel=self.original_sel).search()
        self.original_sel = None
        self._restore_sel()

    def on_change(self, s):
        if s in ("/", "?"):
            return
        self._restore_sel()
        SearchImpl(self.view, s, remember=False, start_sel=self.original_sel).search()

    def on_cancel(self):
        self._restore_sel()
        self.original_sel = None

    def _restore_sel(self):
        self.view.erase_regions("vi_search")
        if not self.original_sel:
            return
        self.view.sel().clear()
        for s in self.original_sel:
            self.view.sel().add(s)
        self.view.show(self.view.sel()[0])
