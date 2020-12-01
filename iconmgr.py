from pathlib import Path
from PyQt5.QtGui import QIcon


class IconMgr:
    ICON_DIR = 'd.png'
    ICON_FILE = 'f.png'

    def __init__(self, basedir, scheme=None):
        self.basedir = Path(basedir) / 'assets'
        self.scheme_enum = tuple(i.parts[-2] for i in self.basedir.glob(f'*/{self.ICON_DIR}'))
        self.scheme_ptr = None
        self.scheme_dict = {}
        if self.scheme_enum:
            if scheme in self.scheme_enum:
                self.update_scheme(scheme)
            if not self.scheme_dict:
                self.update_scheme(self.scheme_enum[0])

    def load_scheme(self, scheme):
        scheme_dir = self.basedir / scheme
        if scheme_dir.is_dir():
            return {'dir': QIcon(str(scheme_dir / self.ICON_DIR)),
                    'file': QIcon(str(scheme_dir / self.ICON_FILE))}

    def update_scheme(self, scheme):
        scheme_icons = self.load_scheme(scheme)
        if scheme_icons:
            self.scheme_dict[scheme] = scheme_icons
            self.scheme_ptr = scheme

    def get(self, icon_type):
        if self.scheme_ptr:
            return self.scheme_dict[self.scheme_ptr].get(icon_type, None)

    def switch_scheme(self, scheme):
        if scheme in self.scheme_dict:
            self.scheme_ptr = scheme
        else:
            self.update_scheme(scheme)
