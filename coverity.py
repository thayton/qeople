#!/usr/bin/env python                                                                                                                                                                
import re
import json
import urllib
import urlparse
import mechanize

from bs4 import BeautifulSoup, Comment, Tag
from readability.readability import Document

COMPANY = {
    'company_name': 'Coverity',
    'company_hq': 'San Francisco, CA',
    'company_url': 'http://www.coverity.com',
    'company_jobs_page_url': 'https://sjobs.brassring.com/1033/ASP/TG/cim_home.asp?partnerid=25235&siteid=5359'
}

def soupify(page):
    s = BeautifulSoup(page)

    # Remove unwanted tags
    tags = s.findAll(lambda tag: tag.name == 'script' or \
                                 tag.name == 'style')
    for t in tags:
        t.extract()
        
    # Remove comments
    comments = s.findAll(text=lambda text:isinstance(text, Comment))
    for c in comments:
        c.extract()

    return s

#
# Inspect page and you will see that they are using the jobs page
# for Synopsys (parent company) and submitting the search form
# with Keyword 'Coverity' to get results on Coverity's jobs page
#
class CoverityJobScraper(object):
    def __init__(self):
        self.br = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))

    def scrape_job_links(self, url):
        jobs = []

        self.br.open(url)
        self.br.follow_link(self.br.find_link(text='Search openings'))

        #
        # self.br.select_form fails with 'ParseError: OPTION outside of SELECT'
        # unless we feed this through BeautifulSoup first!
        #
        soup = soupify(self.br.response().read())
        html = soup.prettify().encode('utf8')
        resp = mechanize.make_response(html, [("Content-Type", "text/html")],
                                       self.br.geturl(), 200, "OK")
        
        self.br.set_response(resp)
        self.br.select_form('frmAgent')
        self.br.form['keyword'] = 'Coverity'
        self.br.submit('submit2')

        pageno = 2

        while True:
            s = soupify(self.br.response().read())
            r = re.compile(r'^cim_jobdetail\.asp\?')

            for a in s.findAll('a', href=r):
                tr = a.findParent('tr')
                td = tr.findAll('td')

                job = {}
                job['title'] = a.text
                job['url'] = self.cleaned_url(a['href'])
                job['location'] = td[3].text
                jobs.append(job)

            a = s.find('a', text='%d' % pageno)
            if not a:
                break # no more pages

            pageno += 1

            #
            # Page 2 link: <a href="javascript:LoadPage(51)">2</a>
            # 
            # function LoadPage(lRecordStart)
            # {
            #   document.frmMassSelect.recordstart.value = lRecordStart;
            #   document.frmMassSelect.JobInfo.value = gstrJobInfo;
            #   document.frmMassSelect.JobSiteInfo.value = gJobSiteInfo;
            #   document.frmMassSelect.sorting.value = "";
            #   document.frmMassSelect.submit();
            # }
            #
            # Clicking on page 2 link Results in FormData:
            #
            #   JobInfo:%%
            #   recordstart:51
            #   sorting:
            #   JobSiteInfo:
            #
            r = re.compile(r'LoadPage\((\d+)')
            m = re.search(r, a['href'])

            self.br.select_form('frmMassSelect')
            self.br.set_all_readonly(False)
            self.br.form['recordstart'] = m.group(1)
            self.br.submit()

        return jobs

    def cleaned_url(self, url):
        '''
        If you try tweeting a job from within the ATS you'll
        see that the permanent url for a job has the format

        https://sjobs.brassring.com/1033/asp/tg/cim_jobdetail.asp?partnerid=25235&siteid=5359&jobid=1121032
        
        You can get the partnerid and siteid from 
        COMPANY['company_jobs_page_url'] and the jobid can be 
        extracted from a['href']. 
        '''
        clean_url = urlparse.urljoin(self.br.geturl(), url)        

        parts = urlparse.urlparse(COMPANY['company_jobs_page_url'])
        params = urlparse.parse_qs(parts.query)
        query_dict = {'partnerid': params['partnerid'][0], 'siteid': params['siteid'][0]}

        parts = urlparse.urlparse(clean_url)        
        params = urlparse.parse_qs(parts.query)
        query_dict.update({'jobid': params['jobId'][0]})

        url_tuple = list(parts)
        url_tuple[4] = urllib.urlencode(query_dict)

        clean_url = urlparse.urlunparse(url_tuple)

        return clean_url

    def scrape_job_descriptions(self, job):
        self.br.open(job['url'])
        
        s = BeautifulSoup(self.br.response().read())
        x = {'name': 'frmJobDetail'}
        f = s.find('form', attrs=x)

        job['description'] = Document(str(f)).summary()

    def scrape(self):
        jobs = self.scrape_job_links(COMPANY['company_jobs_page_url'])
        for job in jobs:
            self.scrape_job_descriptions(job)

        print json.dumps(jobs, indent=2)

if __name__ == '__main__':
    scraper = CoverityJobScraper()
    scraper.scrape()
        
