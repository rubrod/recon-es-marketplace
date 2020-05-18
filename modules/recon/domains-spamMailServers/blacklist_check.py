# module required for framework integration
from recon.core.module import BaseModule
# mixins for desired functionality
from recon.mixins.resolver import ResolverMixin
# module specific imports
import re, dns.resolver, socket

class Module(BaseModule, ResolverMixin):

    meta = {
        'name': 'Blacklist Check',
        'author': 'Rodrigo Baladrón de Juan',
        'version': '',
        'description': '',
        'dependencies': [],
        'files': [],
        'required_keys': [],
        'comments': (),
        'query': {'_source': ['domain'], 'query': {'match': {'type': 'domains'}}},
        'options': (),
    }
    
    def module_run(self, domains):
        blacklists = ['bl.score.senderscore.com', 'bl.mailspike.net', 'bl.spameatingmonkey.net', 'b.barracudacentral.org', 'bl.deadbeef.com', 'bl.spamcop.net', 'blackholes.five-ten-sg.com', 'blacklist.woody.ch', 'bogons.cymru.com', 'cbl.abuseat.org', 'cdl.anti-spam.org.cn', 'combined.abuse.ch', 'combined.rbl.msrbl.net', 'db.wpbl.info', 'dnsbl-1.uceprotect.net', 'dnsbl-2.uceprotect.net', 'dnsbl-3.uceprotect.net', 'dnsbl.inps.de', 'dnsbl.sorbs.net', 'drone.abuse.ch', 'drone.abuse.ch', 'duinv.aupads.org', 'dul.dnsbl.sorbs.net', 'dul.ru', 'dyna.spamrats.com', 'dynip.rothen.com', 'http.dnsbl.sorbs.net', 'images.rbl.msrbl.net', 'ips.backscatterer.org', 'ix.dnsbl.manitu.net', 'korea.services.net', 'misc.dnsbl.sorbs.net', 'noptr.spamrats.com', 'ohps.dnsbl.net.au', 'omrs.dnsbl.net.au', 'orvedb.aupads.org', 'osps.dnsbl.net.au', 'osrs.dnsbl.net.au', 'owfs.dnsbl.net.au', 'owps.dnsbl.net.au', 'pbl.spamhaus.org', 'phishing.rbl.msrbl.net', 'probes.dnsbl.net.au', 'proxy.bl.gweep.ca', 'proxy.block.transip.nl', 'psbl.surriel.com', 'rbl.interserver.net', 'rdts.dnsbl.net.au', 'relays.bl.gweep.ca', 'relays.bl.kundenserver.de', 'relays.nether.net', 'residential.block.transip.nl', 'ricn.dnsbl.net.au', 'rmst.dnsbl.net.au', 'sbl.spamhaus.org', 'short.rbl.jp', 'smtp.dnsbl.sorbs.net', 'socks.dnsbl.sorbs.net', 'spam.abuse.ch', 'spam.dnsbl.sorbs.net', 'spam.rbl.msrbl.net', 'spam.spamrats.com', 'spamlist.or.kr', 'spamrbl.imp.ch', 't3direct.dnsbl.net.au', 'tor.dnsbl.sectoor.de', 'torserver.tor.dnsbl.sectoor.de', 'ubl.lashback.com', 'ubl.unsubscore.com', 'virbl.bit.nl', 'virus.rbl.jp', 'virus.rbl.msrbl.net', 'web.dnsbl.sorbs.net', 'wormrbl.imp.ch', 'xbl.spamhaus.org', 'zen.spamhaus.org', 'zombie.dnsbl.sorbs.net']
        resolver = self.get_resolver()
        for domain in domains:
            try:
                answers = resolver.query(domain, 'MX')
                for rdata in answers:
                    mailServer = str(rdata.exchange).strip('.')
                    try:
                        serverInfo = socket.gethostbyname_ex(mailServer)  
                        IPs = serverInfo[2]
                        for blacklist in blacklists:
                            self.verbose(blacklist)
                            for IP in IPs:
                                reverseIPList = list(reversed(IP.split('.')))
                                reverseIP = ''
                                for i in range(len(reverseIPList)-1):
                                    reverseIP += str(reverseIPList[i]) + '.'
                                reverseIP += reverseIPList[len(reverseIPList)-1]
                                checkURL = reverseIP + '.' + blacklist
                                try:
                                    socket.gethostbyname(checkURL)
                                    self.alert(domain + '\n' + mailServer + '\n' + IP + '\n' + 'Blacklist: ' + blacklist)
                                    self.insert_spamMailServers(domain=domain, mail_server=mailServer, ip=IP, blacklist=blacklist)
                                except socket.gaierror:
                                    pass
                    except socket.gaierror:
                        pass
            except Exception as e:
                self.error(e)
                        


