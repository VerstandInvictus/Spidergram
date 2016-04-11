from bs4 import BeautifulSoup
import requests
import re
import os

#disable warning about HTTPS
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


def getLinksForGalleryPage(url, results, base):
    """
    Recursive function to traverse the script payload that apparently is
    used to load Instagram pages completely on the fly. Pulls each individual
    "page" - which is apparently 49 images by the user, delineated by the
    "start_cursor" and "end_cursor" in the payload - so that it can be parsed
    for images, and then uses the ending cursor to generate the link to the
    next "page".
    """
    print "Have {1} results. Scanning {0}...".format(url, len(results))
    gallery = requests.get(url).content
    galsoup = BeautifulSoup(gallery, "html.parser")
    imglink = galsoup.find_all('script')
    for each in imglink:
        if each.string:
            if each.string.startswith('window._sharedData'):
                payloadRaw = each.string.split(' = ')[1]
                payloadRaw = re.sub('/', '', payloadRaw)
                payload = re.findall('https.*?\.jpg', payloadRaw)
                for link in payload:
                    # they're using some sort of JSON-derived format that is
                    # not parseable by simplejson or yaml, so we need to fix
                    # the weird '\/' escape sequences manually
                    result = re.sub(
                        '\\\\\\\\',
                        '\\\\',
                        link)
                    result = re.sub(
                        's:\\\\',
                        's:\\\\\\\\',
                        result)
                    results.append(result)
                hasNextId = re.search(
                    '(?<=has_next_page"\:)[truefals]*',
                    payloadRaw)
                if hasNextId.group(0) == "true":
                    nextId = re.search(
                        '(?<=end_cursor"\:")[0-9]*',
                        payloadRaw)
                    nextUrl = base + "?max_id=" + nextId.group(0)
                    getLinksForGalleryPage(nextUrl, results, base)
                else:
                    return results


if __name__ == "__main__":
    # start with the gallery page
    baseurl = "https://www.instagram.com/13thwitness/"
    username = baseurl.split('/')[-2]
    results = list()
    getLinksForGalleryPage(baseurl, results, baseurl)

