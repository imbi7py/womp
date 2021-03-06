import time
from gevent.greenlet import Greenlet


class Input(Greenlet):

    retries = 3

    def __init__(self, page_info, wapiti_client, *args, **kwargs):
        self.info = page_info
        self.wapiti = wapiti_client
        self.debug = kwargs.pop('debug', False)
        self.attempts = 0
        self.fetch_results = None
        self.results = None
        self.times = {'create': time.time()}
        super(Input, self).__init__(*args, **kwargs)

    @property
    def class_name(self):
        return str(self.__class__.__name__)

    @property
    def import_name(self):
        return '.'.join((str(self.__module__), str(self.__class__.__name__)))

    @property
    def durations(self):
        ret = {}
        try:
            ret['total'] = self.times['complete'] - self.times['create']
        except:
            pass
        try:
            ret['fetch'] = self.times['fetch_end'] - self.times['fetch_start']
        except:
            pass
        try:
            ret['process'] = self.times['process_end'] - self.times['process_start']
        except:
            pass
        return ret

    @property
    def status(self):
        ret = {}
        ret['attempts'] = self.attempts
        ret['is_complete'] = self.results is not None or self.attempts >= self.retries
        ret['fetch_succeeded'] = self.fetch_results is not None
        if self.results:
            ret['failed_stats'] = dict([(sname, unicode(sres))
                                        for sname, sres in self.results.iteritems()
                                        if isinstance(sres, Exception)])
        else:
            ret['failed_stats'] = {}
        ret['is_successful'] = ret['is_complete'] and ret['fetch_succeeded'] and not ret['failed_stats']
        return ret

    def fetch(self):
        raise NotImplemented  # TODO: convert to abstract class?

    def process(self, fetch_results):
        ret = {}
        for k, func in self.stats.iteritems():
            try:
                full_key = '{0}_{1}'.format(self.prefix, k)
            except AttributeError:
                full_key = k
            try:
                res = func(fetch_results)
            except Exception as e:
                if self.debug:
                    import traceback
                    traceback.print_exc()
                ret[full_key] = e
            else:
                ret[full_key] = res
        return ret

    def __call__(self):
        if self.debug:
            # print '~~', self.info.title, ':', 'fetching', self.class_name
            pass
        self.times['fetch_start'] = time.time()
        for i in range(0, self.retries):
            try:
                self.fetch_results = self.fetch()
            except Exception as e:
                e_msg = (u'Fetch failed on {i_t} input for '
                         'article {p_t} ({p_id}) with exception {e}')
                e_msg = e_msg.format(p_t=self.info.title,
                                     p_id=self.info.page_id,
                                     i_t=self.class_name,
                                     e=repr(e))
                print e_msg
                #import pdb;pdb.post_mortem()
            else:
                break
            finally:
                self.times['fetch_end'] = self.times['process_start'] = time.time()
                self.attempts += 1
        if self.fetch_results is not None:
            self.results = self.process(self.fetch_results)
            if isinstance(self.results, Exception):
                print type(self), 'process step glubbed up on', self.page_title
            self.times['process_end'] = self.times['complete'] = time.time()
        return self.results

    _run = __call__


class WikipediaInput(Input):
    pass
