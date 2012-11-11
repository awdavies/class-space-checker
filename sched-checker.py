#!/usr/bin/env python2
'''
TODO LIST (Apart from inline todos)

* Functions are a bit silly.  Refactor things so this can all run in a loop.

* We need to handle errors for when we can't connect.

* What determines if we can't connect?  Is there a timeout we'll deal with?
  What is it?!

* In the interest of making the install easy for most folks, this is all done in
  regex.  Perhaps consider an easy way to reimplement this using standard (-ish)
  DOM parsers (n either python or another language).

* Now that we have BeautifulSoup, all of the gross regex code should be phased
  out ASAP.

'''
from BeautifulSoup import BeautifulSoup

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

def parse_options():
     #Create instance of OptionParser Module, included in Standard Library
    p = optparse.OptionParser(
        description='Checks space in SLN classes',
        prog='sched-checker',
        version='0.1',
        usage= '%prog [username] [pass]'
    )
    p.add_option('--user','-u', help='User name')
    p.add_option('--password', '-p', help='Password')
    p.add_option('--ssn', '-s', help='Class SSN Number')

    options, arguments = p.parse_args()

    # Decode to the appropriate base.
    if options.user and options.password and options.ssn:
        return options
    p.print_help()
    sys.exit(1)

def send_get_request(url):
    '''
    Gets the page with a get request and returns the string representation of
    said page.

    TOOD: Add get parameters in case we can't simply send it as a post for some
    reason (look up examples of this sort of thing occuring as well, just in
    case any valid GET request with parameters ends up being okay as a POST
    request as well).
    '''
    request = urllib2.Request(url=url, data=None, headers=HTTP_HEADERS)
    response = urllib2.urlopen(request)
    html_str = response.read()
    return html_str

def parse_hidden_params(html_str):
    '''
    They have a bunch of bogus parameters sent
    through the website once you log in for the
    first time.  We'll need to get the whole page and
    parse through turning each one of these into the
    member of a dictionary so that we can get through
    with the post.
    '''
    params = {}
    matches = re.split(r'(\<input\s+type="?hidden"?[^\>]+\>)', html_str)
    for line in matches:
        p = re.match(r'^.*?name="?(?P<name>[^"]+?)"?\s+value="(?P<value>[^"]+?)"', line)
        if p:
            params[p.group('name')] = p.group('value')
    return params

def parse_redirect_action(html_str):
    '''
    This is meant to handle the case when the user has to be redirected by one
    of those silly "continue" buttons.  It usually has a link under the
    parameter labeled "action" and we need to parse it out of there.

    This is making a huge assumption: That we're only going to encounter one
    redirecto button on the page.  This might (maybe) need to be remedied later.
    '''
    #
    #  <form method=post action="https://weblogin.washington.edu" name=relay>
    #
    html_str = "".join(html_str.splitlines())
    regex = re.compile(r'^.*?\<form\s+method="?post"?\s+action="(?P<link>[^"]+?)"\s+name="?relay')
    match = regex.match(html_str)

    if match:
        return match.group('link')
    else:
        return ""

def set_url_opener():
    '''
    Builds a cookie-lovin, url openin machine (pretty simple, but the
    implementation may change later, so it's a function).

    Returns a CookieJar class that is tied to the url opener, just in case
    we wish to peer into the cookie jar later.
    '''
    cookies = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cookies)
    url_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    urllib2.install_opener(url_opener)
    return cookies

def send_post_request(params, link):
    '''
    Attempts to open the link using a post request with the passed dictionary of
    params.

    TODO: Document exceptions.
    '''
    post_data_encoded = urllib.urlencode(params)
    request = urllib2.Request(link, post_data_encoded, HTTP_HEADERS)
    return urllib2.urlopen(request)

def build_schedule_params(qtr_index, sln):
    '''
    Builds the parameters for the schedule page.  The params returned will not
    be encoded and will simply be a python dictionary (so that we can check for
    debugging.  Handling the encoding should be done when loading the web page).
    '''
    year = datetime.datetime.now().year
    qtr = QUARTERS[qtr_index]
    if qtr_index == 3:   # if this is winter, we'll be lookin at next year.
        year += 1
    params = {}
    params['QTRYR'] = "{0} {1}".format(qtr, year)
    params['SLN'] = sln
    return params

def parse_course_info(html_str):
    '''
    This is for parsing the class info on the ASP pages hosted by UW.
    Since they all follow a basic format, we should be able to go through
    and find out the three things we want to know:

    * The class title (for display, and for if/when we decide to send this thing
      to people's emails.

    * The capacity for the class.

    * The enrollment count for the class.

    From these three things we should be able to get all the data we need.  If
    not, then we'll simply add more things for which we will try to parse.
    '''

    return None

def main():
    # Set the cookie handler so we can pass around cookies 
    # from the POST request.  TODO: Should we pass in the cookie jar
    # to be able to read it later?  If we're automating and this is
    # all in a loop, we'll need to be able to clear expired cookies.
    cookies = set_url_opener()
    opts = parse_options()

    ##### STAGE 1: LOGIN
    login_params = parse_hidden_params(
        send_get_request(WEBLOGIN_URL), 
    )
    login_params['user'] = opts.user
    login_params['pass'] = opts.password

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    send_post_request(login_params, WEBLOGIN_URL)

    ##### STAGE 2: GO THROUGH REDIRECTS 
    #
    # Build params for the schedule page.
    # Then query the schedule page.
    sched_params = build_schedule_params(3, opts.ssn)   # TODO: Hard coded!  Change after debugging.
    response = send_post_request(sched_params, SCHEDULE_URL)
    html_str = response.read()

    # Now that we're here, we don't give a crap about javascript, so we'll need
    # to refresh the page with the silly fake cookie they gave us.
    #
    # Then we'll have to go through one more button and that should be it.
    redir_params = parse_hidden_params(html_str)
    redirect_link = parse_redirect_action(html_str)
    response = send_post_request(redir_params, redirect_link)
    html_str = response.read()

    ##### STAGE 3: GET PAGE FOR SSN
    #
    final_params = parse_hidden_params(html_str)
    # This is a bit of a hack.  The page requires 'get args'
    final_params['get_args'] = urllib.urlencode(sched_params)
    redirect_link = parse_redirect_action(html_str)
    response = send_post_request(final_params, redirect_link)
    html_str = response.read()
    print html_str

    ##### STAGE 4: PARSE PAGE FOR ENROLLMENT COUNT
    # If we're here, then we have the page!
    info = parse_course_info(html_str)
    print '\n////////////////////////////////////////////////////\n'
    print info


if __name__ == '__main__':
    main()
    #parse_course_info(open('test.html', 'r').read())
