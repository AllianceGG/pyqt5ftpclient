import sys
from os.path import abspath, dirname, isdir, join
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QAbstractItemView, QTableView, QListView,
                             QLineEdit, QPushButton, QComboBox,
                             QFileSystemModel,
                             QHBoxLayout, QVBoxLayout, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex, QAbstractTableModel
from ftpmgr import FTPMgr
from iconmgr import IconMgr


class FTPTableModel(QAbstractTableModel):
    def __init__(self, json_file_path, parent=None):
        super().__init__(parent)
        self.ftp_mgr = FTPMgr.from_json(json_file_path)
        self.ftp_col_num = len(FTPMgr.attribs) + 1
        self.ftp_content_list = self.get_ftp_list()
        self.icon_mgr = IconMgr(parent.local_path)

    def get_ftp_list(self):
        return [(name, *(facts.get(attrib, '') for attrib in FTPMgr.attribs))
                for name, facts in self.ftp_mgr.do_ls(print_stdout=False)]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.ftp_content_list[index.row()][index.column()]
        if role == Qt.DecorationRole and index.column() == 0:
            return self.icon_mgr.get(self.ftp_content_list[index.row()][1])

    def rowCount(self, index):
        return len(self.ftp_content_list)

    def columnCount(self, index):
        return self.ftp_col_num

    def sort(self, col, order):
        self.layoutAboutToBeChanged.emit()
        self.ftp_content_list.sort(key=lambda e: e[col], reverse=order != Qt.AscendingOrder)
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def refresh(self, refresh_content=True):
        self.layoutAboutToBeChanged.emit()
        if refresh_content:
            self.ftp_content_list = self.get_ftp_list()
            self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.layoutChanged.emit()


class Demo(QWidget):
    def __init__(self, json_file_path):
        super().__init__()

        # Set local fs
        self.local_path = abspath(dirname(__file__))
        self.local_path_view = QLineEdit(self.local_path, self)
        self.local_path_view.returnPressed.connect(self.local_change_path_lineedit)

        self.local_model = QFileSystemModel(self)
        self.local_view = QTableView(self)
        self.local_view.setModel(self.local_model)
        self.local_view.horizontalHeader().setStretchLastSection(True)
        self.local_view.setSortingEnabled(True)
        self.local_view.doubleClicked.connect(self.local_double_clicked)

        self.local_change_path()

        # Set ftp
        self.ftp_par_btn = QPushButton('..', self)
        self.ftp_par_btn.clicked.connect(self.ftp_go_par)

        self.ftp_dl_btn = QPushButton('dl', self)
        self.ftp_dl_btn.clicked.connect(self.ftp_dl)

        self.ftp_model = FTPTableModel(json_file_path, self)
        self.ftp_view = QTableView(self)
        self.ftp_view.setModel(self.ftp_model)
        self.ftp_view.horizontalHeader().setStretchLastSection(True)
        self.ftp_view.setSortingEnabled(True)
        self.ftp_view.doubleClicked.connect(self.ftp_double_clicked)

        self.ftp_path_edit = QLineEdit(self.ftp_model.ftp_mgr.ftp_pwd, self)
        self.ftp_path_edit.returnPressed.connect(self.ftp_change_path_lineedit)

        self.ftp_icon_toggle_box = QComboBox(self)
        self.ftp_icon_toggle_box.addItems(self.ftp_model.icon_mgr.scheme_enum)
        self.ftp_icon_toggle_box.setCurrentText(self.ftp_model.icon_mgr.scheme_ptr)
        self.ftp_icon_toggle_box.currentTextChanged.connect(self.ftp_icon_toggle)

        # Set up layout
        h_layout = QHBoxLayout()
        # left half for ftp
        ftp_v_layout = QVBoxLayout()
        ftp_top_layout = QGridLayout()
        ftp_top_layout.addWidget(self.ftp_par_btn, 0, 0)
        ftp_top_layout.addWidget(self.ftp_path_edit, 0, 1, 1, 15)
        ftp_top_layout.addWidget(self.ftp_dl_btn, 0, 16)
        if self.ftp_model.icon_mgr.scheme_ptr:
            ftp_top_layout.addWidget(self.ftp_icon_toggle_box, 0, 17)
        else:
            self.ftp_icon_toggle_box.setVisible(False)
        ftp_v_layout.addLayout(ftp_top_layout)
        ftp_v_layout.addWidget(self.ftp_view)
        # right half for local fs
        local_v_layout = QVBoxLayout()
        local_v_layout.addWidget(self.local_path_view)
        local_v_layout.addWidget(self.local_view)
        # whole program view:
        h_layout.addLayout(ftp_v_layout)
        h_layout.addLayout(local_v_layout)
        self.setLayout(h_layout)
        self.resize(2000, 1800)

    @pyqtSlot()
    def local_change_path_lineedit(self):
        """ Change local path by user input from QLineEdit """
        new_path = self.local_path_view.text()
        if new_path == self.local_path:  # TODO force new_path as abspath
            return
        if isdir(new_path):
            self.local_path = new_path
            self.local_change_path(False)
        else:
            self.local_path_view.setText(self.local_path)

    def local_change_path(self, change_lineedit=True):
        """ Change local path to self.local_path """
        if change_lineedit:
            self.local_path_view.setText(self.local_path)
        self.local_model.setRootPath(self.local_path)
        self.local_view.setRootIndex(self.local_model.index(self.local_path))
        self.local_model.layoutChanged.emit()

    @staticmethod
    def item_0(item):
        return item if item.column() == 0 else item.siblingAtColumn(0)

    @pyqtSlot(QModelIndex)
    def local_double_clicked(self, item):
        """ Change local path if another dir is double clicked """
        if item.isValid():
            new_path = join(self.local_path, self.item_0(item).data())
            if isdir(new_path):
                self.local_path = new_path
                self.local_change_path()

    @pyqtSlot(QModelIndex)
    def ftp_double_clicked(self, item):
        if item.isValid():
            item_0 = self.item_0(item)
            if item_0.siblingAtColumn(1).data() == 'dir':
                self.ftp_model.ftp_mgr.do_cwd(item_0.data())
                self.ftp_model.refresh()
                self.ftp_path_edit.setText(self.ftp_model.ftp_mgr.ftp_pwd)

    @pyqtSlot()
    def ftp_go_par(self):
        old_dir = self.ftp_model.ftp_mgr.ftp_pwd  # old (current) dir
        self.ftp_model.ftp_mgr.do_cwd('..')
        if self.ftp_model.ftp_mgr.ftp_pwd == old_dir:  # early exit if no real change
            return
        self.ftp_model.refresh()
        self.ftp_path_edit.setText(self.ftp_model.ftp_mgr.ftp_pwd)

    @pyqtSlot()
    def ftp_dl(self):
        for row in {i.row() for i in self.ftp_view.selectedIndexes()}:
            getattr(self.ftp_model.ftp_mgr,
                    f'do_dl_{self.ftp_model.index(row, 1).data()}',
                    lambda: None)(self.ftp_model.index(row, 0).data(), self.local_path)

    @pyqtSlot()
    def ftp_change_path_lineedit(self):
        """ Change ftp path by user input from QLineEdit """
        new_path = self.ftp_path_edit.text()
        old_path = self.ftp_model.ftp_mgr.ftp_pwd
        try:
            self.ftp_model.ftp_mgr.do_cwd(new_path)
            self.ftp_model.refresh()
        except Exception as err:
            print('[ERR] cannot change ftp path to', new_path, ':', err)
            self.ftp_model.ftp_mgr.do_cwd(old_path)
            self.ftp_model.refresh()
            self.ftp_path_edit.setText(old_path)
            self.ftp_model.ftp_mgr.ftp_pwd = old_path

    @pyqtSlot(str)
    def ftp_icon_toggle(self, icon_style):
        self.ftp_model.icon_mgr.switch_scheme(icon_style)
        self.ftp_model.refresh(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Demo(sys.argv[1])
    d.show()
    sys.exit(app.exec_())
