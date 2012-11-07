import re
import urllib
import urllib2

# This will send a post request to weblogin.washington.edu so we can have the
# public cookie for the website.  Afterwards, we can spam the SLN numbers of
# the site.  Later we should make it so that we can log in with command line
# parameters.

# This will be where we log in.
url = "https://weblogin.washington.edu/"

# Some fake headers so they think we have JS and the like.
HTTP_HEADERS = {"User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)"}

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

def login_get():
    '''
    Gets the login page with a get request (so we can parse the bogus header
    values that determine how long we've been on the page and such).
    '''
    request = urllib2.Request(url=url, data=None, headers=HTTP_HEADERS)
    response = urllib2.urlopen(request)
    html_str = response.read()
    return html_str

def params_parse(msg):
    matches = re.split(r'(\<input\s+type="hidden".*?\>)', msg)
    params = {}
    for line in matches:
        p = re.match(r'^.*?name="(?P<name>.*?)"\s+value="(?P<value>.*?)"', line)
        if p:
            params[p.group('name')] = p.group('value')
    return params

def main():
# These will be used later for posting data!
# post_data_encoded = urllib.urlencode(post_data)
# request = urllib2.Request(url, post_data_encoded, HTTP_HEADERS)
# response = urllib2.urlopen(request)
    login_page = login_get()
    params = params_parse(login_page)
    params['user'] = post_data['user']
    params['password'] = post_data['password']
    post_data_encoded = utllib.urlencode(params)
    print params

if __name__ == '__main__':
    main()
