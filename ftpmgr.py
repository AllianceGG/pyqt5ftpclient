from json import load
from ftplib import FTP
from os import makedirs
from os.path import dirname, join, expanduser


class FTPMgr:
    """
    Wrapper of ftplib.FTP:
    In a GUI context, path jump contains "go to a child dir" & "go to parent".
    Therefore, cwd's arg can only be 'child_dirname' or '..'
    """
    attribs = ('type', 'size', 'modify')

    @classmethod
    def from_json(cls, json_file):
        """ Create FTPMgr obj by a json file """
        with open(expanduser(json_file)) as f:
            return cls(**load(f))

    def __init__(self, addr, username='', password='', timeout=10, encoding=''):
        self.ftp = FTP(addr, username, password, timeout=timeout)
        if encoding:
            self.ftp.encoding = encoding
        print(addr, 'welcome msg:', self.ftp.getwelcome(), '\nConnected\n')
        # Save remote current dir name in mem TODO is it safe to assume init dir = / ?
        self.ftp_pwd = '/'

    def do_cwd(self, relative_dir):
        self.ftp_pwd = dirname(self.ftp_pwd) if relative_dir == '..' else join(self.ftp_pwd, relative_dir)
        self.ftp.cwd(relative_dir)

    def do_ls(self, remote_path='.', print_stdout=True):
        try:
            mlsd_ret = self.ftp.mlsd(remote_path, facts=self.attribs)
            if print_stdout:
                for i in mlsd_ret:
                    print(*i)
            else:
                return mlsd_ret
        except Exception as mlsd_err:
            print('mlsd failed', mlsd_err, 'try to ls current dir on ftp')
            self.ftp.dir()

    # In a GUI context, only items under ftp_pwd are available for user
    # interaction, so downloaders below assume items exist inside ftp_pwd

    def do_dl_file(self, filename, local_working_dir='.'):
        try:
            with open(join(local_working_dir, filename), 'wb') as fout:
                self.ftp.retrbinary(f'RETR {filename}', fout.write)
        except Exception as dl_err:
            print('[ERR] cannot download', filename, 'in', local_working_dir, dl_err)

    def do_dl_dir(self, remote_dirname, local_where='.'):
        """ mkdir -p dirname locally and keep same struct """
        local_working_dir = join(local_where, remote_dirname)
        makedirs(local_working_dir, exist_ok=True)

        self.do_cwd(remote_dirname)
        for ftp_item_name, ftp_item_info in self.do_ls(print_stdout=False):
            if ftp_item_info['type'] == 'file':
                self.do_dl_file(ftp_item_name, local_working_dir)
            elif ftp_item_info['type'] == 'dir':
                self.do_dl_dir(ftp_item_name, local_working_dir)
            else:
                print('item', ftp_item_name, 'type', ftp_item_info['type'], 'unknown, thus skip')
        self.do_cwd('..')
