# module required for framework integration
from recon.core.module import BaseModule
# mixins for desired functionality
from recon.mixins.resolver import ResolverMixin
from recon.mixins.threads import ThreadingMixin
# module specific imports
import os, re, requests, bs4, time, datetime, dateparser

class Module(BaseModule):

    meta = {
        'name': 'Posts',
        'author': 'Rodrigo Baladrón de Juan',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': [],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['name'], 'query': {'match': {'type': 'brands'}}},
        'options': (
            ('date', None, False, 'Last hour, day, week, month or year: h, d, w, m, y'),
        ),
    }
    
    def module_run(self, brands):
        date = self.options['date']
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for brand in brands:
            self.pastebin(brand, date, headers)
            self.gistGithub(brand, headers)

    def pastebin(self, brand, date, headers):
        url = 'https://www.google.es/search?q=site:pastebin.com -site:deals.pastebin.com -site:pastebin.com/u/ "' + brand + '"&filter=0'
        if date:
            url += '&tbs=qdr:' + date
        while url:
            try:
                res = requests.get(url, headers=headers, timeout=5)
                res.raise_for_status()
                soup = bs4.BeautifulSoup(res.text, features='lxml')
                notFound = soup.select('.obp')
                if not notFound:
                    elemsGoogle = soup.select('.r > a:first-of-type')
                    for i in range(len(elemsGoogle)):
                        pasteUrl = elemsGoogle[i].get('href')
                        res = requests.get(pasteUrl, headers=headers , timeout=5)
                        try:
                            res.raise_for_status()
                            pasteParse = bs4.BeautifulSoup(res.text,'lxml')
                            title = pasteParse.find('title')
                            pasteTitle = title.text
                            date = pasteParse.select('.paste_box_line2 > span[title]')
                            dateParse = dateparser.parse(date[0].getText())
                            dateDMY = dateParse.strftime("%d/%m/%Y")
                            rawContent = pasteParse.select('textarea[id="paste_code"]')[:32767]
                            self.alert(pasteTitle + '\n' + pasteUrl + '\n' + dateDMY)
                            self.insert_pastes(title=pasteTitle, url=pasteUrl, date=dateDMY, content=rawContent)
                        except Exception as e:
                            self.error(e)
                    url = soup.find('a', id='pnnext')
                    if url:
                        url = 'https://www.google.es/' + url['href'] 
                    else:
                        self.verbose('No next page.')
                        break
                else:
                    self.verbose('Not Found.')
                    break
            except Exception as e:
                self.error(e)
                break

    def gistGithub(self, brand, headers):
        url = 'https://gist.github.com/search?q=' + '"' + brand + '"'
        while url:
            try:
                res = requests.get(url, headers=headers, timeout=5)
                res.raise_for_status()
                soup = bs4.BeautifulSoup(res.text, features='lxml')
                elemsGithub = soup.select('.link-overlay')
                for x in range(len(elemsGithub)):
                    try:
                        pasteUrl = elemsGithub[x].get('href')
                        res = requests.get(pasteUrl, headers=headers, timeout=5)
                        res.raise_for_status()
                        gistParse = bs4.BeautifulSoup(res.text,'lxml')
                        title = gistParse.find('title')
                        pasteTitle = title.text
                        date = gistParse.find('time-ago')
                        dateParse = dateparser.parse(date.getText())
                        dateDMY = dateParse.strftime("%d/%m/%Y")
                        urlRaw = elemsGithub[x].get('href').replace('github', 'githubusercontent') + '/raw'
                        res = requests.get(urlRaw, headers=headers, timeout=5)
                        res.raise_for_status()
                        rawContent = res.text[:32767]
                        self.alert(pasteTitle + '\n' + pasteUrl + '\n' + dateDMY)
                        self.insert_pastes(title=pasteTitle, url=pasteUrl, date=dateDMY, content=rawContent)
                    except Exception as e:
                        self.error(e)
                url = soup.select('a.next_page')
                if url:
                    url = 'https://gist.github.com' + url[0].get('href')  
                else:
                    self.verbose('No next page.')
                    break
            except Exception as e:
                self.error(e)
                break