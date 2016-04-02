from .. import Feeder
from .. import Parser
from .. import Crawler
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
import logging
import re


class GreedyFeeder(Feeder):

    def feed(self, domains):
        if isinstance(domains, str):
            self.domains = [domains]
        elif isinstance(domains, list):
            self.domains = domains
        else:
            self.error('domains must be a string or a list')
        for domain in self.domains:
            self.put_url_into_queue('http://' + urlsplit(domain).geturl())


class GreedyParser(Parser):

    def __init__(self, url_queue, task_queue, session, dup_filter_size=0):
        self.pattern = re.compile(r'http(.*)\.(jpg|jpeg|png|bmp|gif|ico)')
        super(GreedyParser, self).__init__(url_queue, task_queue,
                                           session, dup_filter_size)

    def is_in_domain(self, url, domains):
        for domain in domains:
            if domain in url:
                return True
        return False

    def parse(self, response, feeder):
        soup = BeautifulSoup(response.content, 'lxml')
        tags = soup.find_all('img', src=True)
        for tag in tags:
            if re.match(self.pattern, tag['src']):
                self.put_task_into_queue(dict(img_url=tag['src']))
        tags = soup.find_all(href=True)
        for tag in tags:
            href = tag['href']
            if re.match(self.pattern, href):
                self.put_task_into_queue(dict(img_url=href))
            elif href[0:10] == 'javascript':
                continue
            elif href.split('.')[-1] in ['xml', 'css', 'js', 'txt', 'json']:
                continue
            elif self.is_in_domain(href, feeder.domains):
                if href[0:2] == '//':
                    href = 'http:' + href
                feeder.put_url_into_queue(href)


class GreedyImageCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(GreedyImageCrawler, self).__init__(
            img_dir, feeder_cls=GreedyFeeder,
            parser_cls=GreedyParser, log_level=log_level)

    def crawl(self, domains, max_num=0, parser_thr_num=1, downloader_thr_num=1):
        super(GreedyImageCrawler, self).crawl(
              1, parser_thr_num, downloader_thr_num,
              feeder_kwargs={'domains': domains},
              parser_kwargs={'feeder': self.feeder},
              downloader_kwargs={'max_num': max_num})
