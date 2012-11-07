import urllib
import urllib2

# This will send a post request to weblogin.washington.edu so we can have the
# public cookie for the website.  Afterwards, we can spam the SLN numbers of
# the site.  Later we should make it so that we can log in with command line
# parameters.

url = "https://weblogin.washington.edu/"
http_headers = {"User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)"}

# Change this later!
post_data = {
    "user": "sirlancelot", 
    "password": "SpamandEggs",
}

'''
    They have a bunch of bogus parameters sent
    through the website once you log in for the
    first time.  We'll need to get the whole page and
    parse through turning each one of these into the
    member of a dictionary so that we can get through
    with the post.
'''

def main():

post_data_encoded = urllib.urlencode(post_data)

request = urllib2.Request(url=url, data=None, headers=http_headers)
response = urllib2.urlopen(request)

html_string = response.read()

#request = urllib2.Request(url, post_data_encoded, http_headers)
#response = urllib2.urlopen(request)
print html_string
