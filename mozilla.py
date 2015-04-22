#!/usr/bin/env python                                                                                                                                                                
import re
import json
import urlparse
import mechanize

from bs4 import BeautifulSoup
from readability.readability import Document

COMPANY = {
    'company_name': 'Mozilla',
    'company_hq': 'Mountain View, CA',
    'company_url': 'http://www.mozilla.com',
    'company_jobs_page_url': 'http://careers.mozilla.org/en-US/listings/'
}

class MozillaJobScraper(object):
    def __init__(self):
        self.br = mechanize.Browser()

    def scrape_job_links(self, url):
        jobs = []

        self.br.open(url)

        s = BeautifulSoup(self.br.response().read())
        x = {'class': 'position'}

        for tr in s.findAll('tr', attrs=x):
            td = tr.findAll('td')
            td = { x['class'][0]: x for x in td }

            job = {}
            job['title'] = td['title'].a.text
            job['url'] = urlparse.urljoin(self.br.geturl(), td['title'].a['href'])
            job['location'] = td['location'].text
            job['type'] = td['type'].text
            jobs.append(job)

        return jobs

    def scrape_job_descriptions(self, job):
        self.br.open(job['url'])
        
        s = BeautifulSoup(self.br.response().read())
        n = s.find('section', id='job')

        job['description'] = Document(str(n)).summary()

        x = {'class': re.compile(r'ga-job-listing-apply')}
        a = s.find('a', attrs=x)

        job['how_to_apply'] = a.prettify()

    def scrape(self):
        jobs = self.scrape_job_links(COMPANY['company_jobs_page_url'])
        for job in jobs:
            self.scrape_job_descriptions(job)

        print json.dumps(jobs, indent=2)

if __name__ == '__main__':
    scraper = MozillaJobScraper()
    scraper.scrape()
        
