'''
TODO LIST (Apart from inline todos)

* Functions are a bit silly.  Refactor things so this can all run in a loop.

* We need to handle errors for when we can't connect.

* What determines if we can't connect?  Is there a timeout we'll deal with?
  What is it?!

* In the interest of making the install easy for most folks, this is all done in
  regex.  Perhaps consider an easy way to reimplement this using standard (-ish)
  DOM parsers (n either python or another language).

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
        params = parse_hidden_params(
            weblogin_get_html(), 
        )
        params['user'] = options.user
        params['pass'] = options.password
        return params

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
    '''
    cookies = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cookies)
    url_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    urllib2.install_opener(url_opener)
    return cookies

def send_post_request(params, link):
    '''
    Logs the user into weblogin.
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
    if qtr_index == 3:   # if this is winter.
        year += 1
    params = {}
    params['QTRYR'] = "{0} {1}".format(qtr, year)
    params['SLN'] = sln
    return params

def main():
    ''' 
    Gets the cookies from the WEBLOGIN_URL using the passed params.
    '''
    # Set the cookie handler so we can pass around cookies 
    # from the POST request.  TODO: Should we pass in the cookie jar
    # to be able to read it later?  If we're automating and this is
    # all in a loop, we'll need to be able to clear expired cookies.
    cookies = set_url_opener()
    login_params = controller()  # Params from the GET sent to weblogin.

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    send_post_request(login_params, WEBLOGIN_URL)

    # Build params for the schedule page.
    # Then query the schedule page.
    sched_params = build_schedule_params(3, 10180)   # TODO: Hard coded!  Change after debugging.
    response = send_post_request(sched_params, SCHEDULE_URL)
    html_str = response.read()
    print '-----------------------------------------------\n'

    # Now that we're here, we don't give a crap about javascript, so we'll need
    # to refresh the page with the silly fake cookie they gave us.
    #
    # Then we'll have to go through one more button and that should be it.
    redir_params = parse_hidden_params(html_str)
    redirect_link = parse_redirect_action(html_str)
    response = send_post_request(redir_params, redirect_link)
    html_str = response.read()
    print html_str
    print '-----------------------------------------------\n'

    final_params = parse_hidden_params(html_str)
    # This is a bit of a hack.  The page requires 'get args'
    final_params['get_args'] = urllib.urlencode(sched_params)
    print final_params['get_args']
    redirect_link = parse_redirect_action(html_str)
    response = send_post_request(final_params, redirect_link)

    # If we're here, then we have the page!

if __name__ == '__main__':
    main()
