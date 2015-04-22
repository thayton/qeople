#!/usr/bin/env python                                                                                                                                                                
import re
import json
import urlparse
import mechanize

from bs4 import BeautifulSoup
from readability.readability import Document

COMPANY = {
    'company_name': 'Expect Labs',
    'company_hq': 'San Francisco, CA',
    'company_url': 'https://www.expectlabs.com',
    'company_jobs_page_url': 'http://www.jobscore.com/jobs2/expectlabs/'
}

# JobScore
class ExpectLabsJobScraper(object):
    def __init__(self):
        self.br = mechanize.Browser()
        self.br.addheaders = [('User-agent', 
                               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')]

    def scrape_job_links(self, url):
        jobs = []

        self.br.open(url)

        s = BeautifulSoup(self.br.response().read())
        d = s.find('div', id='js-jobs')
        x = {'class': 'js-job-listing'}

        for tr in s.findAll('tr', attrs=x):
            td = tr.findAll('td')

            job = {}
            job['title'] = td[0].a.text
            job['url'] = urlparse.urljoin(self.br.geturl(), tr.a['href'])
            job['location'] = td[-1].text
            jobs.append(job)

        return jobs

    def scrape_job_descriptions(self, job):
        self.br.open(job['url'])
        
        s = BeautifulSoup(self.br.response().read())
        x = {'class': 'js-job-posting'}
        d = s.find('div', attrs=x)

        job['description'] = Document(str(d)).summary()

        x = {'class': 'js-btn js-btn-apply'}
        a = s.find('a', attrs=x)

        job['how_to_apply'] = a.prettify()

    def scrape(self):
        jobs = self.scrape_job_links(COMPANY['company_jobs_page_url'])
        for job in jobs:
            self.scrape_job_descriptions(job)

        print json.dumps(jobs, indent=2)

if __name__ == '__main__':
    scraper = ExpectLabsJobScraper()
    scraper.scrape()
        
