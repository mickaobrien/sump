import firebase
import libtorrent as lt
import time
import sys
import os
from utility import move_file, get_all_files, move_all_files, hashify, create_dirs
from settings import BASE_URL, SAVE_PATH, DIRS, FINAL_DIRS

#TODO move url, file paths into separate file


class Sump():
    def __init__(self):
        self.db = firebase.Firebase(BASE_URL)
        self.db.uniquify()
        self.set_data()
        self.create_session()
        self.params = {
                'save_path': SAVE_PATH,
                'storage_mode': lt.storage_mode_t(2),
                'paused': False,
                'auto_managed': True,
                'duplicate_is_error': True
                }
        create_dirs(DIRS.values() + FINAL_DIRS.values())
        self.add_torrents(self.undownloaded)

    def watch(self):
        while(1):
            if self.downloading():
                sys.stdout.write('\r%s' % ', '.join(self.downloading()))
                sys.stdout.flush()
            time.sleep(10)
            self.set_data()
            self.add_torrents(self.unstarted)
            if self.downloaded():
                self.remove_completed()

    def set_data(self):
        self.data = self.db.data()
        self.undownloaded = self.get_undownloaded()
        self.unstarted = self.get_unstarted()

    def downloading(self):
        torrents = self.session.get_torrents()
        return ['%s (%f%%)' % (t.name(), t.status().progress*100) 
                for t in torrents if not t.is_finished()]

    def downloaded(self):
        torrents = self.session.get_torrents()
        return ['%s' % t.name()
                for t in torrents if t.is_finished()]

    def create_session(self):
        session = lt.session()
        session.start_dht()
        self.session = session
        
    def get_undownloaded(self):
        data = self.data
        undownloaded = {}
        for k,v in data.iteritems():
            if not data[k]['downloaded']:
                undownloaded[k] = v
        return undownloaded

    def get_unstarted(self):
        data = self.data
        unstarted = {}
        for k,v in data.iteritems():
            if not data[k]['started']:
                unstarted[k] = v
        return unstarted

    def add_torrents(self, torrents):
        for key in torrents:
            self.start_download(key)

    def add_torrent(self, magnet_url, torrent_type):
        handle = lt.add_magnet_uri(self.session, magnet_url, self.params)
        return hashify(handle.info_hash().to_string())

    def start_download(self, key):
        entry = self.data[key]
        url = entry['link']
        info_hash = self.add_torrent(url, entry['type'])
        updated = self.db.update(key, '{"started":true, "hash":"%s"}' % info_hash)
        if updated:
            entry['hash'] = info_hash
            entry['started'] = True
        else:
            raise ValueError

    def remove_completed(self):
        torrents = self.session.get_torrents()
        finished_torrents = [t for t in torrents if t.is_finished()]
        
        if not finished_torrents:
            return

        names = ['%s' % t.name() for t in finished_torrents]
        hashes = [hashify(t.info_hash().to_string()) for t in finished_torrents]

        for t in finished_torrents:
            self.session.remove_torrent(t)

        keys = [self.key_from_hash(h) for h in hashes]
        for k, name in zip(keys, names):
            self.db.update(k, '{"downloaded":true}')
            #move downloaded stuff from paths based on type
            self.organise_file(name, self.data[k]['type'])
        self.rename_files()
        self.move_renamed()

    def rename_files(self):
        os.system('filebot -rename -r --format "../{movie}/{movie}" %s -non-strict' % DIRS['movie'])
        os.system('filebot -rename -r --format "../{n}/Season {s}/{s00e00} - {t}" %s -non-strict' % DIRS['tv'])

    def move_renamed(self):
        move_all_files(DIRS['movie'], FINAL_DIRS['movie'])
        move_all_files(DIRS['tv'], FINAL_DIRS['tv'])

    def organise_file(self, name, media_type):
        original_path = os.path.join(self.params['save_path'], name)
        new_path = DIRS[media_type]
        move_file(original_path, new_path)

    def key_from_hash(self, info_hash):
        return [k for k in self.data 
                if self.data[k]['hash']==info_hash][0]


if __name__=='__main__':
    s = Sump()
    s.watch()
