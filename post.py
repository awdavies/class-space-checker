'''
TODO LIST (Apart from inline todos)

* Functions are a bit silly.  Refactor things so this can all run in a loop.

* We need to handle errors for when we can't connect.

* What determines if we can't connect?  Is there a timeout we'll deal with?
  What is it?!

'''
import cookielib
import datetime
import optparse
import re
import sys
import urllib
import urllib2

# These are the current known strings for time schedule quarters.
# for now we'll have to have the user specify which one is which.
# (Spring and Summer I just made up).
QUARTERS = ['SPR', 'SUM', 'AUT', 'WIN',]

# This will be where we log in.
WEBLOGIN_URL = "https://weblogin.washington.edu/"

# This is the url for the time schedule server (ASP... gross).
SCHEDULE_URL = "https://sdb.admin.washington.edu/timeschd/uwnetid/sln.asp"

# Some fake headers so they think we have JS and the like.
HTTP_HEADERS = {
    "User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT) AppleWebKit/537.6+ (KHTML, like Gecko) WebKitGTK+/1.10.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def controller():
     #Create instance of OptionParser Module, included in Standard Library
    p = optparse.OptionParser(
        description='Checks space in SLN classes',
        prog='sched-checker',
        version='0.1',
        usage= '%prog [username] [pass]'
    )
    p.add_option('--user','-u', help='User name')
    p.add_option('--password', '-p', help='Password')

    options, arguments = p.parse_args()

    # Decode to the appropriate base.
    if options.user and options.password:
        return parse_weblogin_params(
            weblogin_get_html(), 
            options.user, 
            options.password,
        )

    p.print_help()
    sys.exit(1)

def weblogin_get_html():
    '''
    Gets the login page with a get request (so we can parse the bogus header
    values that determine how long we've been on the page and such).
    '''
    request = urllib2.Request(url=WEBLOGIN_URL, data=None, headers=HTTP_HEADERS)
    response = urllib2.urlopen(request)
    html_str = response.read()
    return html_str

def parse_weblogin_params(html_str, user, password):
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

def login_weblogin(params):
    '''
    Logs the user into weblogin.
    '''
    post_data_encoded = urllib.urlencode(params)
    request = urllib2.Request(WEBLOGIN_URL, post_data_encoded, HTTP_HEADERS)
    return urllib2.urlopen(request)

def build_schedule_params(qtr_index, sln):
    '''
    Builds the parameters for the schedule page.  The params returned will not
    be encoded and will simply be a python dictionary (so that we can check for
    debugging.  Handling the encoding should be done when loading the web page).
    '''
    year = datetime.datetime.now().year
    qtr = QUARTERS[qtr_index]
    if qtr_index == 3:   # if this is winter.
        year += 1
    params = {}
    params['QTRYR'] = "{0} {1}".format(qtr, year)
    params['SLN'] = sln
    return params

def get_schedule_page_html(params):
    post_data_encoded = urllib.urlencode(params)
    print SCHEDULE_URL + post_data_encoded
    request = urllib2.Request(SCHEDULE_URL, post_data_encoded, HTTP_HEADERS)
    return urllib2.urlopen(request)

def parse_schedule_params(html_str):
    params = {}
    params['user']     = user
    params['pass'] = password
    matches = re.split(r'(\<input\s+type="hidden".*?\>)', html_str)
    for line in matches:
        p = re.match(r'^.*?name="(?P<name>.*?)"\s+value="(?P<value>.*?)"', line)
        if p:
            params[p.group('name')] = p.group('value')

    return params

def main():
    ''' 
    Gets the cookies from the WEBLOGIN_URL using the passed params.
    '''
    # Set the cookie handler so we can pass around cookies 
    # from the POST request.  TODO: Should we pass in the cookie jar
    # to be able to read it later?  If we're automating and this is
    # all in a loop, we'll need to be able to clear expired cookies.
    set_url_opener()
    params = controller()  # Params from the GET sent to weblogin.

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    response = login_weblogin(params)
    print response.read()   # to check we've logged in (debug.  remove later.)

    print '-----------------------------------------------\n'

    # Build params for the schedule page.
    params = build_schedule_params(3, 10180)   # TODO: Hard coded!  Change after debugging.
    response = get_schedule_page_html(params)
    print response.read()

    # Now that we're here, we don't give a crap about javascript, so we'll need
    # to refresh the page with the silly fake cookie they gave us.

    print '-----------------------------------------------\n'

if __name__ == '__main__':
    main()
