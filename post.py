import re
import optparse
import sys
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

def controller():
     #Create instance of OptionParser Module, included in Standard Library
    p = optparse.OptionParser(description='Checks space in SLN classes',
                              prog='sched-checker',
                              version='0.1',
                              usage= '%prog [username] [pass]')
    p.add_option('--user','-u', help='User name')
    p.add_option('--password', '-p', help='Password')

    options, arguments = p.parse_args()

    # Decode to the appropriate base.
    if options.user and options.password:
        return params_parse(login_get(), user=options.user,
                            password=options.password)

    p.print_help()
    sys.exit(1)


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

def params_parse(html_str, user, password):
    matches = re.split(r'(\<input\s+type="hidden".*?\>)', html_str)
    params = {}
    for line in matches:
        p = re.match(r'^.*?name="(?P<name>.*?)"\s+value="(?P<value>.*?)"', line)
        if p:
            print p.group('name') + ": " + p.group('value')
            params[p.group('name')] = p.group('value')

    params['user']     = user
    params['password'] = password
    return params

def main():
    params = controller()
    post_data_encoded = urllib.urlencode(params)

    # Get the url again with a POST
    #request = urllib2.Request(url, post_data_encoded, HTTP_HEADERS)
    #response = urllib2.urlopen(request)
    print params
    #print response.read()

if __name__ == '__main__':
    main()
