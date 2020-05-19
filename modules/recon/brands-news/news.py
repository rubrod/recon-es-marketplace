# module required for framework integration
from recon.core.module import BaseModule
# module specific imports
import requests, bs4, re, dateparser

class Module(BaseModule):

    meta = {
        'name': 'News',
        'author': 'Rubén Álvarez Elena',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': [],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['name'], 'query': {'match': {'type': 'brands'}}},
        'options': (
            ('date', None, False, 'Last hour, day, week, month or year: h, d, w, m, y'),
            ('country', False, False, 'ES'),
        ),
    }

    def module_run(self, brands):
        date = self.options['date']
        country = self.options['country']
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for brand in brands:
            url = 'https://www.google.es/search?q=' + '"' + brand + '"' + '&tbm=nws'
            if date and country:
                url += '&tbs=qdr:' + date + ',ctr:countryES&cr=countryES'
            elif date:
                url += '&tbs=qdr:' + date
            elif country:
                url += '&tbs=ctr:countryES&cr=countryES'
            while url:
                try:
                    res = requests.get(url, headers=headers, timeout=5)
                    res.raise_for_status()
                    soup = bs4.BeautifulSoup(res.text, features='lxml')
                    notFound = soup.select('.obp')
                    if not notFound:
                        news = soup.select('.l')
                        newsDates = soup.select('.dhIWPd')
                        for i in range(len(news)):
                            try:
                                newsURL = news[i].get('href')
                                newsDate = re.sub(r'.*-', '', newsDates[i].getText())
                                dateDMY = dateparser.parse(newsDate).strftime("%d/%m/%Y")
                                res = requests.get(newsURL, headers=headers, timeout=5)
                                res.raise_for_status()
                                soupWeb = bs4.BeautifulSoup(res.text, features='lxml')
                                title = soupWeb.find('title')
                                if title is not None:
                                    if title.getText() != '':
                                        newsTitle = title.getText().strip()
                                    else:
                                        newsTitle = news[i].getText()
                                else:
                                    newsTitle = news[i].getText()
                                self.alert(newsTitle + '\n' + newsURL + '\n' + dateDMY)
                                self.insert_news(title=newsTitle, url=newsURL, date=dateDMY)
                            except Exception as e:
                                self.error(e)
                        url = soup.find('a', id='pnnext')
                        if url:
                            url = 'https://www.google.es/' + url['href']
                        else:
                            self.verbose('The End.')
                            break
                    else:
                        self.verbose('Not Found.')
                        break
                except Exception as e:
                    self.error(e)
                    break