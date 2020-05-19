# module required for framework integration
from recon.core.module import BaseModule
# module specific imports
import requests, json

class Module(BaseModule):

    meta = {
        'name': 'Emails Hunter',
        'author': 'Rubén Álvarez Elena',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': [],
        'required_keys': ['hunter_api'],
        'comments': (),
        'query': {'_source': ['domain'], 'query': {'match': {'type': 'domains'}}},
        'options': (),
    }

    def module_run(self, domains):
        apiKey = self.keys['hunter_api']
        for domain in domains:
            url = 'https://api.hunter.io/v2/domain-search?domain=' + domain + '&api_key=' + apiKey + '&limit=100'
            try:
                res = requests.get(url, timeout=5)
                res.raise_for_status()
                jsonData = json.loads(res.text)
                numEmails = 0
                while numEmails < jsonData['meta']['results']:
                    emails = jsonData['data']['emails']
                    for i in range(len(emails)):
                        email = emails[i]['value']
                        sources = emails[i]['sources']
                        for j in range(len(sources)):
                            sourceURL = sources[j]['uri']
                            self.alert(email + '\n' + sourceURL)
                            self.insert_emails(email=email, source=sourceURL)
                    numEmails += len(emails)
                    if numEmails < jsonData['meta']['results']:
                        url += '&offset=' + str(numEmails)
                        res = requests.get(url, timeout=5)
                        res.raise_for_status()
                        jsonData = json.loads(res.text)
            except Exception as e:
                self.error(e)