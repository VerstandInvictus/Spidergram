from bs4 import BeautifulSoup
import requests
import re
import os
import codecs
import unidecode
import arrow

# disable warning about HTTPS
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


class instaLogger:
    def __init__(self, logfile):
        self.logfile = logfile

    def logEntry(self, entry, level):
        with codecs.open(self.logfile, mode='a', encoding='utf-8') as log:
            log.write(entry + '\n')
        if 'progress' in level:
            print unidecode.unidecode(entry)


class instagram:
    def __init__(self, logobj):
        self.logger = logobj
        self.dest = os.path.join(os.getcwdu(), 'images')
        if not os.path.exists(self.dest):
            os.makedirs(self.dest)
        self.results = None
        self.resetResults()
        self.baseUrl = None

    def resetResults(self):
        self.results = dict(
            count=0,
            skipped=0,
            failed=0,
            succeeded=0,
            nonexistent=0,
        )

    def setBaseUrl(self, url):
        # storing base URL simplifies recursion
        self.baseUrl = url

    def downloadImage(self, imgurl, dest=None):
        # download an image, avoiding duplication.
        imgname = imgurl.split('/')[-1]
        if not dest:
            rdest = self.dest
        else:
            rdest = os.path.join(self.dest, dest)
        imgwrite = os.path.join(rdest, imgname)
        try:
            if not os.path.exists(imgwrite):
                r = requests.get(imgurl)
                with open(imgwrite, "wb") as code:
                    code.write(r.content)
                self.logger.logEntry(('downloaded ' + imgname), 'progress')
                self.results['succeeded'] += 1
                return True
            else:
                self.logger.logEntry(('already have ' + imgname),
                                     'verbose')
                self.results['skipped'] += 1
                return True
        except:
            self.logger.logEntry('failed to get: {0} from {1}'.format(
                imgurl, imgname), 'verbose')
            self.results['failed'] += 1
            return None

    def findWindowSharedData(self, pageurl):
        page = requests.get(pageurl).content
        soup = BeautifulSoup(page, "html.parser")
        scripts = soup.find_all('script')
        for each in scripts:
            if each.string:
                if each.string.startswith('window._sharedData'):
                    return each.string.split(' = ')[-1]

    def getLinksForGalleryPage(self, url):
        """
        Recursive function to traverse the script payload that apparently is
        used to load Instagram pages completely on the fly. Pulls each individual
        "page" - which is apparently 49 images by the user, delineated by the
        "start_cursor" and "end_cursor" in the payload - so that it can be parsed
        for images, and then uses the ending cursor to generate the link to the
        next "page".
        """
        username = baseurl.split('/')[-2]
        print "Downloaded {1} images. Scanning {0}...".format(
            url, self.results['succeeded'])
        payloadRaw = self.findWindowSharedData(url)
        payloadRaw = re.sub('/', '', payloadRaw)
        postIds = re.findall(
            '(?<=\{"code":").*?"',
            payloadRaw)
        for code in postIds:
            hrlink = self.getHighResLink(code[:-1])
            self.downloadImage(hrlink, dest=username)
        hasNextId = re.search(
            '(?<=has_next_page":)[truefals]*',
            payloadRaw)
        if hasNextId.group(0) == "true":
            nextId = re.search(
                '(?<=end_cursor":")[0-9]*',
                payloadRaw)
            nextUrl = self.baseUrl + "?max_id=" + nextId.group(0)
            self.getLinksForGalleryPage(nextUrl)
        else:
            return

    def getHighResLink(self, code):
        pageurl = 'https://www.instagram.com/p/{0}/?hl=en'.format(code)
        payloadRaw = self.findWindowSharedData(pageurl)
        hrlink = re.findall(
            '(?<="display_src":").*?\?',
            payloadRaw)[0]
        hrlink = hrlink.replace('\\', '')[:-1]
        return hrlink


if __name__ == "__main__":
    dt = arrow.utcnow().to('US/Pacific').format('YYYY-MM-DD')
    logfile = os.path.join('logs', str('spidergram ' + dt + '.log'))
    logger = instaLogger(logfile)
    site = instagram(logger)
    baseurl = "https://www.instagram.com/13thwitness/"
    site.setBaseUrl(baseurl)
    site.getLinksForGalleryPage(baseurl)

