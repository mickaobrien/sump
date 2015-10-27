from collections import OrderedDict
import requests

KEEP_LAST = 60


class Firebase():
    def __init__(self, url):
        self.url = url
        self.clean()

    def data(self):
        data_url = '%s/.json' % self.url
        request = requests.get(data_url)
        return request.json()

    def update(self, key, data):
        update_url = '%s%s/.json' % (self.url, key)
        r = requests.patch(update_url, data=data)
        return r.ok

    def delete(self, key):
        url = '%s%s.json' % (self.url, key)
        r = requests.delete(url)
        return r.ok

    def uniquify(self):
        """ Deletes extra copies of same link. """
        data = self.data()
        keys = data.keys()
        links = [data[k]['link'] for k in data]
        multiple_links = set([l for l in links if links.count(l) > 1])
        for link in multiple_links:
            multiple_keys = [key for key in keys if data[key]['link'] == link]
            for key in multiple_keys[1:]:
                self.delete(key)

    def ordered_data(self):
        sorted_data = sorted(self.data().items(), key=lambda x: x[1]['created'])
        return OrderedDict(sorted_data)

    def clean(self):
        ordered_data = self.ordered_data()
        if len(ordered_data) > KEEP_LAST:
            number_to_delete = len(ordered_data) % KEEP_LAST
            keys = ordered_data.keys()[:number_to_delete]
            for key in keys:
                if ordered_data[key]['downloaded']:
                    self.delete(key)
