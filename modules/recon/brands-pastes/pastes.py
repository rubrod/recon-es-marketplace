# module required for framework integration
from recon.core.module import BaseModule
# mixins for desired functionality
from recon.mixins.resolver import ResolverMixin
from recon.mixins.threads import ThreadingMixin
# module specific imports
import os, re, requests, bs4, time, datetime, dateparser
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class Module(BaseModule):

    meta = {
        'name': 'Posts',
        'author': 'Rodrigo Baladrón de Juan',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': ['geckodriver'],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['name'], 'query': {'match': {'type': 'brands'}}},
        'options': (
            ('driver', os.path.join(BaseModule.data_path, 'geckodriver'), True, 'path to selenium driver'),
        ),
    }
    
    def module_run(self, brands):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for brand in brands:
            self.pastebin(brand, headers)
            self.gistGithub(brand, headers)

    def pastebin(self, brand, headers):
        driverPath = self.options['driver']
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(executable_path=driverPath, options=options)
        url ='https://pastebin.com/search?q=' + '"' + brand + '"'
        try:
            driver.get(url)
            pages = driver.find_elements_by_class_name('gsc-cursor-page')
            urls = []
            i = 0
            while True:
                elems = driver.find_elements_by_class_name('gs-per-result-labels')
                for elem in elems:
                    url = elem.get_attribute('url')
                    if url is not None:
                        urlRegex = re.compile(r'^(?:http|https)://pastebin.+')
                        urls += urlRegex.findall(url)
                pages = driver.find_elements_by_class_name('gsc-cursor-page')
                if i != len(pages)-1 and len(pages) != 0:
                    pages[i+1].click()
                    i += 1
                    time.sleep(1)
                else:
                    break
            if urls: 
                for url in urls: 
                    try: 
                        res = requests.get(url, headers=headers, timeout=5)
                        res.raise_for_status()
                        pasteParse = bs4.BeautifulSoup(res.text,'lxml')
                        title = pasteParse.find('title')
                        pasteTitle = title.text
                        date = pasteParse.select('.paste_box_line2 > span[title]')
                        dateParse = dateparser.parse(date[0].getText())
                        dateDMY = dateParse.strftime("%d/%m/%Y")
                        rawContent = pasteParse.select('textarea[id="paste_code"]')[:32767]
                        self.alert(pasteTitle + '\n' + url + '\n' + dateDMY)
                        self.insert_pastes(title=pasteTitle, url=url, date=dateDMY, content=rawContent)
                    except Exception as e:
                        self.error(e)
        except Exception as e:
            self.error(e)

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
   