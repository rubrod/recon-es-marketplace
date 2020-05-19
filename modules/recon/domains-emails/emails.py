# module required for framework integration
from recon.core.module import BaseModule
# module specific imports
import requests, bs4, re, io, PyPDF2

class Module(BaseModule):

    meta = {
        'name': 'Emails',
        'author': 'Rubén Álvarez Elena',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': [],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['domain'], 'query': {'match': {'type': 'domains'}}},
        'options': (
            ('date', None, False, 'Last hour, day, week, month or year: h, d, w, m, y'),
        ),
    }

    def module_run(self, domains):
        date = self.options['date']
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for domain in domains:
            emailRegex = re.compile(r'[a-zA-ZñÑáéíóúÁÉÍÓÚ0-9._%-]+@' + re.escape(domain))
            url = 'https://www.google.es/search?q=' + '"@' + domain + '"' + '&filter=0'
            if date:
                url += '&tbs=qdr:' + date
            while url:
                try:
                    res = requests.get(url, headers=headers, timeout=5)
                    res.raise_for_status()
                    soup = bs4.BeautifulSoup(res.text, features='lxml')
                    notFound = soup.select('.obp')
                    if not notFound:
                        results = soup.select('.r > a:first-of-type')
                        for x in range(len(results)):
                            try:
                                resultURL = results[x].get('href')
                                res = requests.get(resultURL, headers=headers, timeout=5)
                                res.raise_for_status()
                                if '.pdf' in resultURL.lower():
                                    f = io.BytesIO(res.content)
                                    pdfReader = PyPDF2.PdfFileReader(f)
                                    numPages = pdfReader.getNumPages()
                                    emailList = []
                                    for y in range(numPages):
                                        pageObj = pdfReader.getPage(y)
                                        page = pageObj.extractText()
                                        emails = emailRegex.findall(page)
                                        if emails is not None:
                                            for email in emails:
                                                if email not in emailList:
                                                    self.alert(email + '\n' + resultURL)
                                                    self.insert_emails(email=email, source=resultURL)
                                                    emailList.append(email)
                                else:
                                    emails = emailRegex.findall(requests.utils.unquote(res.text))
                                    if emails is not None:
                                        emailList = []
                                        for email in emails:
                                            if email not in emailList:
                                                self.alert(email + '\n' + resultURL)
                                                self.insert_emails(email=email, source=resultURL)
                                                emailList.append(email)
                            except Exception as e:
                                self.error(e)
                        url = soup.find('a', id='pnnext')
                        if url:
                            url = 'https://www.google.es' + url['href']
                        else:
                            self.verbose('The End.')
                            break
                    else:
                        self.verbose('Not Found.')
                        break
                except Exception as e:
                    self.error(e)
                    break