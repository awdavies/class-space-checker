#!/usr/bin/env python2
'''
TODO LIST (Apart from inline todos)

* Functions are a bit silly.  Refactor things so this can all run in a loop.

* We need to handle errors for when we can't connect. Throw around exceptions
  and the like for things like bogus SLN numbers, invalid username/password,
  etc.

* If there's no password or username, perhaps just ask for them and have the
  password not show up when it's typed in (like with most other programs.)

* What determines if we can't connect?  Is there a timeout we'll deal with?
  What is it?!

'''
import datetime
import getpass
import optparse
import re
import sys
import urllib
import web_util as wu

# These are the current known strings for time schedule quarters.
# for now we'll have to have the user specify which one is which.
# (Spring and Summer I just made up).
QUARTERS = ['SPR', 'SUM', 'AUT', 'WIN',]

# This will be where we log in.
WEBLOGIN_URL = "https://weblogin.washington.edu/"

# This is the url for the time schedule server (ASP... gross).
SCHEDULE_URL = "https://sdb.admin.washington.edu/timeschd/uwnetid/sln.asp"

# The cookie domains we're interested in.  If these expire, they need to be
# reacquired (that rhymes!).
WEBLOGIN_REGEX = re.compile(r'weblogin.washington.edu', re.IGNORECASE)

SDB_ADMIN_PUB_DOMAIN = 'sdb.admin.washington.edu'
SDB_ADMIN_SESSION_DOMAIN = '.sdb.admin.washington.edu'

def parse_options():

    def sln_callback(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    # Create instance of OptionParser Module, included in Standard Library
    p = optparse.OptionParser(
        description='Checks space in SLN classes',
        prog='sched-checker',
        version='0.1',
        usage= '%prog [username] [pass]',
    )
    p.add_option('--user','-u', help='User name')
    p.add_option(
        '--password', 
        '-p', 
        help='Password. If ommitted, will be requested as user input.'
    )
    p.add_option(
        '--sln', 
        '-s', 
        type='string',
        action="callback", 
        callback=sln_callback, 
        help='Class SLN Number'
    )

    options, arguments = p.parse_args()

    if not options.user:
        setattr(options, 'user', raw_input('[?] UW Netid: '))
    if not options.password:
        setattr(options, 'password', getpass.getpass('[?] Password: '))
    if not options.sln:
        setattr(
            options, 
            'sln', 
            raw_input('[?] Class SLNs (separated by comma, no spaces): ')
        )

    return options

    p.print_help()
    sys.exit(1)

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

def get_schedule_page(sched_params):
    '''
    Logs in through the schedule page by sending a relay to the pub-cookie
    through the relay atop the page.
    '''
    html_str = wu.send_get_request(SCHEDULE_URL, sched_params).read()
    print '=============================================================='
    print html_str
    print '=============================================================='
    params = wu.parse_hidden_params(html_str)
    redirect_link = params['relay_url']
    '''
    Send a post request to the 'document.onload' function using a POST so we can
    get our session id and load the page properly.
    '''
    html_str = wu.send_post_request(redirect_link).read()
    print '=============================================================='
    print html_str

    sys.exit(1)
    '''
    response = wu.send_get_request(SCHEDULE_URL, sched_params)
    html_str = response.read()

    print html_str

    # Now that we're here, we don't give a crap about javascript, so we'll need
    # to refresh the page with the silly fake cookie they gave us.
    #
    # Then we'll have to go through one more button and that should be it.
    redir_params = wu.parse_hidden_params(html_str)
    redirect_link = wu.parse_redirect_action(html_str)
    print redirect_link
    response = wu.send_post_request(redirect_link, redir_params)
    html_str = response.read()


    ##### GET PAGE FOR SLN
    #
    final_params = wu.parse_hidden_params(html_str)
    # This is a bit of a hack.  The page requires 'get args.'  Currently
    # we can't loop around until we finally get redirected through the page.
    # right now this needs to be changed since this exposing implementation
    # details of web_util.py!
    final_params['get_args'] = urllib.urlencode(sched_params)
    redirect_link = wu.parse_redirect_action(html_str)
    print redirect_link
    response = wu.send_post_request(redirect_link, final_params)
    html_str = response.read()
    sys.exit(1)
    return html_str
    '''

def uw_netid_login(netid, password):
    login_params = wu.parse_hidden_params(wu.send_get_request(WEBLOGIN_URL))
    login_params['user'] = netid
    login_params['pass'] = password

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    wu.send_post_request(WEBLOGIN_URL, login_params)

def validate_login_cookie(cookie_jar, user, password):
    '''
    This determines if any of the necessary cookies are expired, and if so, we
    will reacquire them.
    '''
    login = True
    for cookie in cookie_jar:
        if re.match(WEBLOGIN_REGEX, cookie.domain):
            if not cookie.is_expired():
                login = False
    if login:
        uw_netid_login(user, password)

def main():
    # Set the cookie handler so we can pass around cookies 
    # from the POST request.  TODO: Should we pass in the cookie jar
    # to be able to read it later?  If we're automating and this is
    # all in a loop, we'll need to be able to clear expired cookies.
    cookies = wu.set_url_opener()
    opts = parse_options()

    for sln in opts.sln:
        # Make sure none of the cookies are expired.  Re-login if necessary.
        validate_login_cookie(cookies, opts.user, opts.password)

        sched_params = build_schedule_params(3, sln)   # TODO: Hard coded! Change after debugging.
        html_str = get_schedule_page(sched_params)
        
        ##### STAGE 3: PARSE PAGE FOR ENROLLMENT COUNT
        #
        # If we're here, then we have the page!
        #info = wu.parse_table_headers(['SLN', 'Title', 'Enrollment', 'Limit'], html_str)

if __name__ == '__main__':
    main()
