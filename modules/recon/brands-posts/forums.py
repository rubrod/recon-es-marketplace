# module required for framework integration
from recon.core.module import BaseModule
# module specific imports
import os, requests, bs4, re, dateparser, time, datetime
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
            ('date', None, False, 'Last hour, day, week, month or year: h, d, w, m, y'),
        ),
    }

    def module_run(self, brands):
        date = self.options['date']
        elOtroLadoDates = {'h': '', 'd': '1', 'w': '7', 'm': '30', 'y': '365'}
        redditDates = {'h': 'hour', 'd': 'day', 'w': 'week', 'm': 'month', 'y': 'year'}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for brand in brands:
            if date is not None:
                self.elOtroLado(brand, elOtroLadoDates[date], headers)
                self.reddit(brand, redditDates[date], headers)
            else:
                self.elOtroLado(brand, None, headers)
                self.reddit(brand, None, headers)
            self.forocoches(brand, date, headers)

    def elOtroLado(self, brand, date, headers):
        count = 0
        url = 'https://www.elotrolado.net/search.php?sf=all&sr=posts&tips=1&keywords="' + brand + '"'
        if date:
            url += '&st=' + date
        while url:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                soup = bs4.BeautifulSoup(response.text, features='lxml')
                elemsElOtroLado = soup.select('.title')
                if elemsElOtroLado:
                    for i in range(len(elemsElOtroLado)):
                        try:
                            postUrl = 'https://www.elotrolado.net' + elemsElOtroLado[i].get('href')
                            response = requests.get(postUrl, headers=headers, timeout=5)
                            response.raise_for_status()
                            elOtroLadoParse = bs4.BeautifulSoup(response.text,'lxml')
                            title = elOtroLadoParse.find('title')
                            postTitle = title.text
                            dateElem = elOtroLadoParse.select('time')
                            dateParse = dateparser.parse(dateElem[0].get('title'))
                            dateDMY = dateParse.strftime("%d/%m/%Y")
                            self.alert(postTitle + '\n' + postUrl + '\n' + dateDMY)
                            self.insert_posts(title=postTitle, url=postUrl, date=dateDMY)
                        except Exception as e:
                            self.error(e)
                    count += 50
                    url = 'https://www.elotrolado.net/search.php?st=0&sk=t&sd=d&keywords="' + brand + '"&start=' + str(count)
                    if date:
                        url += '&st=' + date
                else:
                    self.verbose('No next page.')
                    break
            except Exception as e:
                self.error(e)
                break

    def reddit(self, brand, date, headers):    
        try:
            driverPath = self.options['driver']
            options = Options()
            options.add_argument('--headless')
            driver = webdriver.Firefox(executable_path=driverPath, options=options)
            url = 'https://www.reddit.com/search/?q="' + brand + '"'
            if date:
                url += '&t=' + date
            driver.get(url)
            lastHeight = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                newHeight = driver.execute_script("return document.body.scrollHeight")
                if newHeight == lastHeight:
                    break
                lastHeight = newHeight
            elems = driver.find_elements_by_class_name('SQnoC3ObvgnGjWt90zD9Z')
            for i in range(len(elems)):
                postUrl = elems[i].get_attribute('href')
                response = requests.get(postUrl, headers=headers, timeout=5)
                redditParse = bs4.BeautifulSoup(response.text,'lxml')
                title = redditParse.select('title')
                postTitle = title[0].getText()
                date = redditParse.select('._3jOxDPIQ0KaOWpzvSQo-1s')
                dateParse = dateparser.parse(date[0].getText())
                dateDMY = dateParse.strftime("%d/%m/%Y")
                self.alert(postTitle + '\n' + postUrl + '\n' + dateDMY)
                self.insert_posts(title=postTitle, url=postUrl, date=dateDMY)
            driver.quit()
        except Exception as e:
            self.error(e)

    def forocoches(self, brand, date, headers):
        url = 'https://www.google.es/search?q=site:forocoches.com "' + brand + '"&filter=0'
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
                    titlesGoogle = soup.select('.r h3')
                    dateGoogle = soup.select('.s')
                    for i in range(len(elemsGoogle)):
                        postUrl = elemsGoogle[i].get('href')
                        res = requests.get(postUrl, headers=headers , timeout=5)
                        try:
                            res.raise_for_status()
                            soupWeb = bs4.BeautifulSoup(res.text, features='lxml')
                            title = soupWeb.find('title')
                            if title != None:
                                if title.getText() != '':
                                    postTitle = title.getText()
                                else:
                                    postTitle = titlesGoogle[i].getText()
                            else:
                                postTitle = titlesGoogle[i].getText()
                            try:
                                dateRegex = re.compile(r'^(\s|\.|\w)* -')
                                dateMatch = dateRegex.search(dateGoogle[i].getText())
                                dateParse = dateparser.parse(str(dateMatch.group(0)))
                                dateDMY = dateParse.strftime("%d/%m/%Y")
                                self.alert(postTitle + '\n' + postUrl + '\n' + dateDMY)
                                self.insert_posts(title=postTitle, url=postUrl, date=dateDMY)
                            except Exception as e:
                                pass
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

