# module required for framework integration
from recon.core.module import BaseModule
# module specific imports
import requests, bs4, io, PyPDF2

class Module(BaseModule):

    meta = {
        'name': 'Docs',
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
            url = 'https://www.google.es/search?q=' + 'site:' + domain + ' ext:pdf OR ext:txt OR ext:rtf OR ext:xml OR ext:csv OR ext:doc OR ext:docx OR ext:xls OR ext:xlsx OR ext:ppt OR ext:pptx OR ext:pps OR ext:ppsx OR ext:odt OR ext:ods OR ext:odp' + '&filter=0'
            if date:
                url += '&tbs=qdr:' + date
            while url:
                try:
                    res = requests.get(url, headers=headers, timeout=5)
                    res.raise_for_status()
                    soup = bs4.BeautifulSoup(res.text, features='lxml')
                    notFound = soup.select('.obp')
                    if not notFound:
                        docs = soup.select('.r > a:first-of-type')
                        for x in range(len(docs)):
                            try:
                                docURL = docs[x].get('href')
                                res = requests.get(docURL, headers=headers, timeout=5)
                                res.raise_for_status()
                                if 'pdf' in res.headers['Content-Type']:
                                    f = io.BytesIO(res.content)
                                    pdfReader = PyPDF2.PdfFileReader(f)
                                    pdfInfo = pdfReader.getDocumentInfo()
                                    metadata = {}
                                    for meta in pdfInfo:
                                        if pdfInfo[meta]:
                                            metadata[meta.strip('/')] = pdfInfo[meta]
                                    self.alert(docURL + '\n' + str(metadata))
                                    self.insert_documents(domain=domain, url=docURL, metadata=metadata)
                                else:
                                    self.alert(docURL)
                                    self.insert_documents(domain=domain, url=docURL)
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