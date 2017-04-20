# -- coding: utf-8 --
import urllib2
import Queue
from urlparse import urlparse, urljoin, urldefrag, urlunparse
from bs4 import BeautifulSoup
from threading import Thread, Lock
import time
import codecs
import w3lib.url
from robotexclusionrulesparser import RobotExclusionRulesParser
import os.path

DOMAIN = 'northwestern.edu' # only consider site ending with DOMAIN
MAX_URLS = 5000000 # stop when there are so many urls in the dict to avoid OOM!
N_workers = 4 # # of threads
global_id = 0 # self increasing
url_tasks = Queue.Queue()
url_ids = {} # url : url_id
transition_file = open('tm_nu.txt', 'w') # transition map: in_id [out_ids]
url_id_file = codecs.open('ids_nu.txt', 'w', encoding="utf-8") # not all urls are ascii
last_update = time.time() # last time any thread is active
write_lock = Lock()
robots_policies = {} # robots.txt info on each site
rp_lock = Lock() # lock for robots_policies
urls_extensions = set() # just for science
skip_file_types = set(['jpg', 'png', 'bmp', 'eps', 'gif', 'jpeg', 'svg', 'tif', 'tiff',
                       'pdf', 'doc', 'docx', 'ppt', 'pptx', 'csv', 'xls', 'xlsx',
                       'mp3', 'mp4', 'swf', 'avi', 'dvi', 'mov', 'mid', 'mpeg', 'mpg',
                       'wav', 'wma', 'wmv', 'm4v',
                       'apk', 'dmg', 'exe', 'msi', 'zip',
                       'ttt',   # what is this?
                       'css', 'js', 'dll']) # skip those file types

class UrlCrawler(Thread):
    def __init__(self, id):
        Thread.__init__(self)
        self.id = id
        self._to_stop = False
        
    def run(self):
        while not self._to_stop:
            try:
                url = url_tasks.get_nowait()
                self.crawl(url)
            except Queue.Empty:
                time.sleep(1)
        print(self.id, 'exiting', self._to_stop, url_tasks.empty())
        
    def stop(self):
        self._to_stop = True
        self.join()
    
    def crawl(self, in_url):
        global global_id, last_update, DOMAIN
        print("Crawler %d on P#%d: %s"%(self.id, url_ids[in_url], in_url))
        try:
            request = urllib2.Request(in_url)
            response = urllib2.urlopen(request, timeout = 5)
            real_url = w3lib.url.canonicalize_url(response.geturl())
            real_uri = urlparse(real_url)
            extension = real_uri.path.lower().split('.')[-1]
            if response.info().maintype != 'text' or extension in skip_file_types:
                content = ''
            else:
                content = response.read()
        except:
            real_url = in_url
            content = ''
        
        if real_url == in_url: # no redirect
            soup = BeautifulSoup(content, "html.parser")
            raw_urls = [link.get('href') for link in soup.find_all('a')]
        else: # redirect
            raw_urls = [real_url]
        
        out_urls = set()
        for url in raw_urls:
            #print('parsing', url)
            if url is None or len(url) <= 1:
                continue
            
            url = url.strip()
            
            if url.startswith('/http://') or url.startswith('/https://'):
                # why would someone do this?
                url = url[1:]
            if url.startswith('mailto:') or url.startswith('mailto@'):
                continue
            
            fixed_url = w3lib.url.canonicalize_url(urljoin(in_url, url))
            if len(fixed_url) > 1000: # long urls tend to be wrong urls
                continue
            uri = urlparse(fixed_url)
            if uri.scheme is not None and uri.scheme not in ['http','https', '']:
                continue
            if uri.hostname is not None:
                if not uri.hostname.endswith(DOMAIN):
                    continue
                elif uri.hostname not in robots_policies:
                    site_rp = RobotExclusionRulesParser()
                    try:
                        site_rp.fetch('http://' + uri.hostname + '/robots.txt', timeout=3)
                    except:
                        print "error with", ('http://' + uri.hostname + '/robots.txt')
                    rp_lock.acquire()
                    robots_policies[uri.hostname] = site_rp
                    rp_lock.release()
                if not (robots_policies[uri.hostname].is_allowed("*", fixed_url)):
                    continue
            extension = uri.path.lower().split('.')[-1]
            if extension in skip_file_types:
                continue
            if 1 < len(extension) < 8 and '/' not in extension:
                urls_extensions.add(extension)
            
            out_urls.add(fixed_url)
        
        #print out_urls
        #get lock
        write_lock.acquire()
        out_ids = []
        for url in out_urls:
            if url in url_ids:
                out_ids.append(url_ids[url])
            else:
                url_ids[url] = global_id
                out_ids.append(global_id)
                url_id_file.write('%d\t%s\n' % (global_id, url))
                url_id_file.flush()
                global_id += 1
                url_tasks.put(url)
        transition_file.write('%d\t%s\n' % (url_ids[in_url], str(out_ids)))
        transition_file.flush()
        last_update = time.time()
        write_lock.release()
        #release lock
        print('%d urls in total reported by %d' % (global_id, self.id))

def manual_add_robot_policies():
    # coz some critical sites have invalid robots.txt
    ## surprised to see SO MANY sites without valid robots.txt!
    site_rp = RobotExclusionRulesParser()
    site_rp.parse('User-agent: * \n' + 'Disallow: /search\n' 
                  + 'Disallow: /advanced_search\n')
    robots_policies['findingaids.library.northwestern.edu'] = site_rp
    
    site_rp = RobotExclusionRulesParser()
    site_rp.parse('User-agent: * \n' + 'Disallow: /catalog\n' + 'Disallow: /contact\n'
                  + 'Disallow: /downloads\n' + 'Disallow: /users\n')
    robots_policies['digitalhub.northwestern.edu'] = site_rp
    
    site_rp = RobotExclusionRulesParser()
    site_rp.parse('User-agent: * \n' + 'Disallow: /catalog\n')
    robots_policies['images.library.northwestern.edu'] = site_rp
    robots_policies['images.northwestern.edu'] = site_rp
    robots_policies['media.northwestern.edu'] = site_rp
    robots_policies['arch.library.northwestern.edu'] = site_rp
    
    site_rp = RobotExclusionRulesParser()
    site_rp.parse('User-agent: * \n' + 'Disallow: /?*\n')
    robots_policies['schedule.radiology.northwestern.edu'] = site_rp
    
    site_rp = RobotExclusionRulesParser()
    try:
        request = urllib2.Request('http://www.ctd.northwestern.edu/robots.txt')
        response = urllib2.urlopen(request, timeout = 5)
        content = response.read()
    except:
        content = 'User-agent: * \n'
    content += ('Disallow: /courses?*\n')
    site_rp.parse(content)
    robots_policies['www.ctd.northwestern.edu'] = site_rp

if __name__ == '__main__':
    global global_id, last_update
    manual_add_robot_policies()
    
    if os.path.isfile('tm_finished.txt') and os.path.isfile('ids_finished.txt'):
        # warm start
        finished_ids = set()
        url_tasks = Queue.Queue()
        global_id = 0
        with open('tm_finished.txt', 'r') as f:
            for line in f:
                line_split = line.strip().split('\t')
                if len(line_split) == 2:
                    start_id, _ = line.split('\t')
                    finished_ids.add(int(start_id))
        with codecs.open('ids_finished.txt', 'r', encoding="utf-8") as f:
            for line in f:
                line_split = line.strip().split('\t')
                if len(line_split) == 2:
                    url_id = int(line_split[0])
                    url_string = str(line_split[1])
                    # print url_id
                    url_ids[url_string] = url_id
                    if url_id not in finished_ids:
                        url_tasks.put(url_string)
                    global_id = max(global_id, url_id + 1)
        del finished_ids
        last_update = time.time()
    else:
        # cold start
        global_id = 0
        start_url = "http://www.northwestern.edu/"
        url_tasks = Queue.Queue()
        url_tasks.put(start_url)
        url_ids[start_url] = 0
        global_id += 1
    
    workers = []
    for i in xrange(N_workers):
        workers.append(UrlCrawler(i+1))
        workers[i].start()
    
    while time.time() - last_update < 120 and global_id < MAX_URLS:
        time.sleep(1)
    print('Stoping', time.time(), last_update)
        
    for i in xrange(N_workers):
        workers[i].stop()
        
    if global_id >= MAX_URLS:
        print('URL limit reached')
    else:
        print('No new url found!')
    
    transition_file.close()
    url_id_file.close()
