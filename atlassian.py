#!/usr/bin/env python                                                                                                                                                                
import re
import json
import urlparse
import mechanize

from bs4 import BeautifulSoup
from readability.readability import Document

COMPANY = {
    'company_name': 'Atlassian',
    'company_hq': 'Sydney, Australia',
    'company_url': 'http://www.atlassian.com',
    'company_jobs_page_url': 'http://chj.tbe.taleo.net/chj02/ats/careers/searchResults.jsp?org=ATLASSIAN&cws=1'
}

class AtlassianJobScraper(object):
    def __init__(self):
        self.br = mechanize.Browser()
        self.br.addheaders = [('User-agent', 
                               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')]

    def scrape_job_links(self, url):
        jobs = []

        self.br.open(url)

        while True:
            s = BeautifulSoup(self.br.response().read())
            r = re.compile(r'requisition\.jsp(;jsessionid=[A-Z0-9]+)?\?')

            for a in s.findAll('a', href=r):
                tr = a.findParent('tr')
                td = tr.findAll('td')

                job = {}
                job['title'] = a.text
                job['url'] = self.cleaned_url(a['href'])
                job['location'] = td[-1].b.text
                jobs.append(job)

            # Pagination
            r = re.compile(r'\d+-\d+')
            b = s.find('b', text=r)
            p = b.parent
            r = re.compile(r'\d+-(\d+) of (\d+)')
            m = re.search(r, p.text)

            if m.group(1) == m.group(2):
                break

            try:
                self.br.follow_link(self.br.find_link(text='>>'))
            except mechanize.LinkNotFoundError:
                break 

        return jobs

    def is_last_page(self, next_page_url):
        '''
        x   y      z
        100-129 of 129
        
        When y == z we're on the last page
        '''
        return curr_page_rowFrom == next_page_rowFrom

    def cleaned_url(self, url):
        ''' 
        Get rid of the jsessionid cruft
        '''
        clean_url = urlparse.urljoin(self.br.geturl(), url)
        clean_url_list = list(urlparse.urlparse(clean_url))
        clean_url_list[3] = ''
        clean_url = urlparse.urlunparse(clean_url_list)

        return clean_url

    def scrape_job_descriptions(self, job):
        self.br.open(job['url'])
        
        s = BeautifulSoup(self.br.response().read())
        x = {'class': 'left job-content'}
        n = s.find('section', attrs=x)

        job['location'] = COMPANY['company_hq']
        job['description'] = Document(str(n)).summary()

        x = {'class': 'apply'}
        n = s.find('section', attrs=x)

        job['how_to_apply'] = n.prettify()

    def scrape(self):
        jobs = self.scrape_job_links(COMPANY['company_jobs_page_url'])
        for job in jobs:
            self.scrape_job_descriptions(job)

        print json.dumps(jobs, indent=2)

if __name__ == '__main__':
    scraper = AtlassianJobScraper()
    scraper.scrape()
        
