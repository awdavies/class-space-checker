import cookielib
import optparse
import re
import sys
import urllib
import urllib2

# These are the current known strings for time schedule quarters.
# for now we'll have to have the user specify which one is which.
QUARTERS = ['AUT', 'WIN',]

# This will be where we log in.
WEBLOGIN_URL = "https://weblogin.washington.edu/"

# UW Time Schedule URL
SCHED_URL = "https://sdb.admin.washington.edu/timeschd/uwnetid/sln.asp"

# Some fake headers so they think we have JS and the like (lol, Windows NT).
HTTP_HEADERS = {"User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)"}

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
        return params_parse(login_get(), options.user, options.password)

    p.print_help()
    sys.exit(1)



def login_get():
    '''
    Gets the login page with a get request (so we can parse the bogus header
    values that determine how long we've been on the page and such).
    '''
    request = urllib2.Request(url=WEBLOGIN_URL, data=None, headers=HTTP_HEADERS)
    response = urllib2.urlopen(request)
    html_str = response.read()
    return html_str

def params_parse(html_str, user, password):
    '''
    They have a bunch of bogus parameters sent
    through the website once you log in for the
    first time.  We'll need to get the whole page and
    parse through turning each one of these into the
    member of a dictionary so that we can get through
    with the post.
    '''
    params = {}
    params['user']     = user
    params['pass'] = password
    matches = re.split(r'(\<input\s+type="hidden".*?\>)', html_str)
    for line in matches:
        p = re.match(r'^.*?name="(?P<name>.*?)"\s+value="(?P<value>.*?)"', line)
        if p:
            params[p.group('name')] = p.group('value')

    return params

def set_url_opener():
    '''
    Builds a cookie-lovin, url openin machine (pretty simple, but the
    implementation may change later, so it's a function).
    '''
    cookies = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cookies)
    url_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    urllib2.install_opener(url_opener)

def main():
    ''' 
    Gets the cookies from the WEBLOGIN_URL using the passed params.
    '''
    params = controller()  # Set params from get request.

    # Set the cookie handler so we can get cookies from the POST request.
    set_url_opener()

    post_data_encoded = urllib.urlencode(params)
    request = urllib2.Request(WEBLOGIN_URL, post_data_encoded, HTTP_HEADERS)

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    response = urllib2.urlopen(request)
    print response.read()   # to check we've logged in (debug.  remove later.)


    

if __name__ == '__main__':
    main()
