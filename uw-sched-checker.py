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
    p.add_option('--sln', '-s', help='Class SLN Number')

    options, arguments = p.parse_args()

    # Decode to the appropriate base.
    if options.user and options.password and options.sln:
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
    response = wu.send_post_request(sched_params, SCHEDULE_URL)
    html_str = response.read()

    # Now that we're here, we don't give a crap about javascript, so we'll need
    # to refresh the page with the silly fake cookie they gave us.
    #
    # Then we'll have to go through one more button and that should be it.
    redir_params = wu.parse_hidden_params(html_str)
    redirect_link = wu.parse_redirect_action(html_str)
    response = wu.send_post_request(redir_params, redirect_link)
    html_str = response.read()

    ##### GET PAGE FOR SLN
    #
    final_params = wu.parse_hidden_params(html_str)
    # This is a bit of a hack.  The page requires 'get args.'  Currently
    # we can't loop around until we finally get redirected through the page.
    final_params['get_args'] = urllib.urlencode(sched_params)
    redirect_link = wu.parse_redirect_action(html_str)
    response = wu.send_post_request(final_params, redirect_link)
    return response.read()

def main():
    # Set the cookie handler so we can pass around cookies 
    # from the POST request.  TODO: Should we pass in the cookie jar
    # to be able to read it later?  If we're automating and this is
    # all in a loop, we'll need to be able to clear expired cookies.
    cookies = wu.set_url_opener()
    opts = parse_options()

    ##### STAGE 1: LOGIN
    login_params = wu.parse_hidden_params(wu.send_get_request(WEBLOGIN_URL))
    login_params['user'] = opts.user
    login_params['pass'] = opts.password

    ''' 
    TODO: Handle a) The WEBLOGIN_URL not opening, b) The username/pass being wrong
    '''
    wu.send_post_request(login_params, WEBLOGIN_URL)

    ##### STAGE 2: GO THROUGH REDIRECTS 
    #
    # Build params for the schedule page.
    # Then query the schedule page.
    sched_params = build_schedule_params(3, opts.sln)   # TODO: Hard coded!  Change after debugging.
    html_str = get_schedule_page(sched_params)
    
    ##### STAGE 3: PARSE PAGE FOR ENROLLMENT COUNT
    #
    # If we're here, then we have the page!
    info = wu.parse_table_headers(['SLN', 'Title', 'Enrollment', 'Limit'], html_str)
    print "CLASS INFO:"
    sorted_keys = info.keys()
    sorted_keys.sort()
    for key in sorted_keys:
        print "\t{0}: {1}".format(key, info[key])

if __name__ == '__main__':
    main()
