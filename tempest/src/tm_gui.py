# vim: set expandtab shiftwidth=4 softtabstop=4:

# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

from chimerax.ui import HtmlToolInstance

class TemplateMatchingTool(HtmlToolInstance):

    # Inheriting from HtmlToolInstance gets us the following attributes
    # after initialization:
    #   self.tool_window: instance of chimerax.ui.MainToolWindow
    #   self.html_view: instance of chimerax.ui.widgets.HtmlView
    # Defining methods in this subclass also trigger some automated callbacks:
    #   handle_scheme: called when custom-scheme link is visited
    #   update_models: called when models are opened or closed
    # If cleaning up is needed on finish, override the ``delete`` method
    # but be sure to call ``delete`` from the superclass at the end.

    SESSION_ENDURING = False    # Does this instance persist when session closes
    SESSION_SAVE = False        # No session saving for now
    CUSTOM_SCHEME = "templatematching"  # Scheme used in HTML for callback into Python
    help = "help:user/tools/tutorial.html"
                                # Let ChimeraX know about our help page

    def __init__(self, session, tool_name):
        # ``session`` - ``chimerax.core.session.Session`` instance
        # ``tool_name``      - string

        # Initialize base class.  ``size_hint`` is the suggested
        # initial tool size in pixels.  For debugging, add
        # "log_errors=True" to get Javascript errors logged
        # to the ChimeraX log window.
        super().__init__(session, tool_name, size_hint=(575, 400),log_errors=True)
        # self.session = session
        # Set name displayed on title bar (defaults to tool_name)
        # Must be after the superclass initialization in order
        # to override the default
        self.display_name = "Tempest"

        self._build_ui()

    def _build_ui(self):
        # Fill in html viewer with initial page in the module
        import os.path
        html_file = os.path.join(os.path.dirname(__file__), "tm_gui.html")
        import pathlib
        self.html_view.setUrl(pathlib.Path(html_file).as_uri())

    def handle_scheme(self, url):
        # ``url`` - ``PyQt5.QtCore.QUrl`` instance

        # This method is called when the user clicks a link on the HTML
        # page with our custom scheme.  The URL path and query parameters
        # are controlled on the HTML side via Javascript.  Obviously,
        # we still do security checks in case the user somehow was
        # diverted to a malicious page specially crafted with links
        # with our custom scheme.  (Unlikely, but not impossible.)
        # URLs should look like: tutorial:cofm?weighted=1

        # First check that the path is a real command
        command = url.path()
        if command == "update_models":
            self.update_models()
            return
        elif command in ["load_database"]:
            # Collect the optional parameters from URL query parameters
            # and construct a command to execute
            from urllib.parse import parse_qs
            query = parse_qs(url.query())
            from .cistem_database import get_tm_results_from_database
            tm_info = get_tm_results_from_database(query['database'][0])
            js = f"tm_info={tm_info.to_json(orient='records')};"
            js+="""
            load_database(tm_info);
            """
            self.html_view.runJavaScript(js)
        elif command in ["load_job_from_database"]:
            from urllib.parse import parse_qs
            query = parse_qs(url.query())
            self.session.logger.info(f"Got event {query}")
            #from chimerax.core.commands import run
            #run(self.session, cmd)
        else:
            from chimerax.core.errors import UserError
            raise UserError("unknown tm command: %s" % command)

    def update_models(self, trigger=None, trigger_data=None):
        # Update the <select> options in the web form with current
        # list of atomic structures.  Also enable/disable submit
        # buttons depending on whether there are any structures open.

        # Get the list of atomic structures
        from chimerax.atomic import AtomicStructure
        options = []
        for m in self.session.models:
            if not isinstance(m, AtomicStructure):
                continue
            options.append((m, m.atomspec))

        # Construct Javascript for updating <select> and submit buttons
        if not options:
            options_text = ""
            disabled_text = "true";
        else:
            options_text = ''.join(['<option value="%s">%s</option>' % (v, t)
                                    for t, v in options])
            disabled_text = "false";
        import json
        js = self.JSUpdate % (json.dumps(options_text), disabled_text)
        self.html_view.runJavaScript(js)

    JSUpdate = """
document.getElementById("model").innerHTML = %s;
var buttons = document.getElementsByClassName("submit");
for (var i = 0; i != buttons.length; ++i) {
    buttons[i].disabled = %s;
}
"""
