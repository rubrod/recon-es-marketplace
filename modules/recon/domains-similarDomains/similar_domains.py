# module required for framework integration
from recon.core.module import BaseModule
# mixins for desired functionality
from recon.mixins.resolver import ResolverMixin
from recon.mixins.threads import ThreadingMixin
# module specific imports
import os, requests, json, binascii, socket, hashlib, time, datetime, tldextract, dns.resolver

class Module(BaseModule, ResolverMixin, ThreadingMixin):

    meta = {
        'name': 'Similar Domains',
        'author': 'Rubén Álvarez Elena',
        'version': '',
        'description': '',
        'dependencies': [],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['domain'], 'query': {'match': {'type': 'domains'}}},
        'options': (
            ('TLDs', os.path.join(BaseModule.data_path, 'TLDs.txt'), False, 'file containing a list of TLDs'),
        ),
        'files': ['TLDs.txt'],
    }

    def module_run(self, domains):
        tldsFile = self.options['TLDs']
        tlds = []
        if os.path.isfile(tldsFile):
            with open(tldsFile) as f:
                tlds = [x.strip() for x in f.read().splitlines()]
        resolver = self.get_resolver()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        for domain in domains:
            domainLabels = tldextract.extract(domain)
            if domainLabels.subdomain:
                domainName = '.'.join(domainLabels[:2])
            else:
                domainName = domainLabels.domain
            domainExt = '.' + domainLabels.suffix
            if not tlds or domainExt not in tlds:
                tlds.append(domainExt)
            for tld in tlds:
                domainTld = domainName + tld
                self.verbose(domainTld)
                domainHex = binascii.hexlify(domainTld.encode())
                url = 'http://dnstwister.report/api/fuzz/' + str(domainHex, 'ascii')
                try:
                    res = requests.get(url, timeout=5)
                    res.raise_for_status()
                    jsonData = json.loads(res.text)
                    similarDomainsDictList = jsonData['fuzzy_domains']
                    similarDomains = []
                    for i in range(len(similarDomainsDictList)):
                        similarDomain = similarDomainsDictList[i]['domain']
                        if similarDomain not in domains:
                            similarDomainLabels = tldextract.extract(similarDomain)
                            if not (domainLabels.subdomain and similarDomainLabels.domain == domainLabels.domain):
                                if similarDomainLabels.subdomain:
                                    similarDomains.append({'similarDomain': similarDomain, 'isSubdomain': True})
                                else:
                                    similarDomains.append({'similarDomain': similarDomain, 'isSubdomain': False})
                    self.thread(similarDomains, domain, resolver, headers)
                except Exception as e:
                    self.error(e)

    def module_thread(self, similarDomainDict, domain, resolver, headers):
        similarDomain = similarDomainDict['similarDomain']
        try:
            answers = resolver.query(similarDomain, 'A')
            ips = []
            for rdata in answers:
                ips.append(rdata.address)
            wildcardRecordMatch = False
            if similarDomainDict['isSubdomain']:
                wildcardSubdomain = '*.' + similarDomain
                attempt = 0
                maxAttempts = 2
                while attempt < maxAttempts:
                    try:
                        answers = resolver.query(wildcardSubdomain, 'A')
                        if answers[0].address in ips:
                            wildcardRecordMatch = True
                        break
                    except Exception:
                        attempt += 1
                        pass
            if not wildcardRecordMatch:
                similarDomainUrl = 'http://' + similarDomain + '/'
                res = requests.head(similarDomainUrl, headers=headers, timeout=5)
                res.raise_for_status()
                if res.status_code not in {301, 302}:
                    try:
                        positives = self.virustotalScan(similarDomain, headers)
                        snapshotURL, screenshotURL = self.archiveSave(similarDomain, headers)
                        self.alert(similarDomain + '\n' + str(ips) + '\n' + 'Positives: ' + str(positives) + '\n' + snapshotURL + '\n' + screenshotURL)
                        self.insert_similarDomains(original_domain=domain, similar_domain=similarDomain, ips=ips, vt_positives=positives, snapshot=snapshotURL, screenshot=screenshotURL)
                    except Exception as e:
                        self.error(e)
        except Exception:
            pass

    def virustotalScan(self, domain, headers):
        domainUrl = 'http://' + domain + '/'
        domainEncoded = domainUrl.encode('utf-8')
        url = 'https://www.virustotal.com/ui/urls/' + hashlib.sha256(domainEncoded).hexdigest() + '/analyse'
        res = requests.post(url, headers=headers, timeout=5)
        res.raise_for_status()
        jsonData = res.json()
        url = 'https://www.virustotal.com/ui/analyses/' + jsonData['data']['id']
        time.sleep(10)
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        analysisData = res.json()
        analysisStatus = analysisData['data']['attributes']['status']
        attempt = 0
        maxAttempts = 5
        while 'queued' in analysisStatus and attempt < maxAttempts:
            time.sleep(1)
            res = requests.get(url, headers=headers, timeout=5)
            res.raise_for_status()
            analysisData = res.json()
            analysisStatus = analysisData['data']['attributes']['status']
            attempt += 1
        analysisStats = analysisData['data']['attributes']['stats']
        positives = int(analysisStats['malicious']) + int(analysisStats['suspicious'])
        return positives

    def archiveSave(self, domain, headers):
        data = {
            'url': domain,
            'capture_screenshot': 'on'
        }
        res = requests.post('https://web.archive.org/save/', data=data, headers=headers, timeout=5)
        res.raise_for_status()
        today = datetime.datetime.utcnow().strftime('%Y%m%d')
        url = 'https://web.archive.org/web/' + today + '/' + domain
        time.sleep(25)
        res = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        res.raise_for_status()
        snapshotURL = res.url
        url = 'https://web.archive.org/web/' + today + 'if_/http://web.archive.org/screenshot/' + domain
        res = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        res.raise_for_status()
        screenshotURL = res.url
        return (snapshotURL, screenshotURL)