#!/usr/bin/env python                                                                                                                                                                

import re
import json
import urlparse
import mechanize

from bs4 import BeautifulSoup
from readability.readability import Document

COMPANY = {
    'company_name': 'Gigwalk',
    'company_hq': 'San Francisco, CA',
    'company_url': 'http://www.gigwalk.com',
    'company_jobs_page_url': 'http://www.gigwalk.com/careers'
}

class GigwalkJobScraper(object):
    def __init__(self):
        self.br = mechanize.Browser()

    def scrape_job_links(self, url):
        jobs = []

        self.br.open(url)

        s = BeautifulSoup(self.br.response().read())
        r = re.compile(r'^jobDescriptions/[^.]+\.html$')

        for a in s.findAll('a', href=r):
            job = {}
            job['title'] = a.text
            job['url'] = urlparse.urljoin(self.br.geturl(), a['href'])
            jobs.append(job)

        return jobs

    def scrape_job_descriptions(self, job):
        self.br.open(job['url'])
        
        s = BeautifulSoup(self.br.response().read())
        d = s.find('div', id='careerBodyContainer')

        job['location'] = d.h6.text
        job['description'] = Document(str(d)).summary()


    def scrape(self):
        jobs = self.scrape_job_links(COMPANY['company_jobs_page_url'])
        for job in jobs:
            self.scrape_job_descriptions(job)

        print json.dumps(jobs, indent=2)

if __name__ == '__main__':
    scraper = GigwalkJobScraper()
    scraper.scrape()
        
