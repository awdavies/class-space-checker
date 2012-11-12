from BeautifulSoup import BeautifulSoup
import cookielib
import re
import urllib
import urllib2

# Some fake headers so we can login properly.
HTTP_HEADERS = {
    "User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT) AppleWebKit/537.6+ (KHTML, like Gecko) WebKitGTK+/1.10.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def send_get_request(url, params={}):
    '''
    Gets the page with a get request and returns the response of
    said page, see docs for urllib and urllib2 to read more about this response
    object.

    TOOD: Add get parameters in case we can't simply send it as a post for some
    reason (look up examples of this sort of thing occuring as well, just in
    case any valid GET request with parameters ends up being okay as a POST
    request as well).
    '''
    get_data_encoded = urllib.urlencode(params)
    if get_data_encoded:
        url = "?".join([url, get_data_encoded])
    
    request = urllib2.Request(url=url, data=None, headers=HTTP_HEADERS)
    response = urllib2.urlopen(request)
    return response

def parse_hidden_params(html_str):
    '''
    This is to deal with all of the hidden form parameters (which are likely for
    csrf safety).  These are returned as a dictionary of names to values
    (intended to be used as parameters for 'send_post_request').

    If no hidden parameters are found, an empty dictionary will be returned.
    '''

    params = {}
    page = BeautifulSoup(html_str)
    inputs = [p for p in page.findAll('input') if p['type'] == u'hidden']
    for input_ in inputs:
        params[input_['name']] = input_['value']
    return params

def parse_redirect_action(html_str):
    '''
    This is meant to handle the case when the user has to be redirected by one
    of those silly 'document.onload' functions.  It's usually just sending a
    form with a bunch of hidden parameters.

    Note this will only work if there is one form on the page.  It will refuse
    to work if there is no 'onload' function atop the page that ends in a submit
    function.
    '''

    # This should probably make sure the page is a link to UW weblogin
    # or maybe even simpler, like checking to see if it links to a different
    # page, or a set of pages which happens to include UW weblogin.
    page = BeautifulSoup(html_str)
    form = page.form
    body = page.body
    try:
        submit_func = body['onload']
    except KeyError:
        return None
    if not re.match(r'^.*?submit\(\)$', submit_func):
        return None

    if form is not None:
        try:
            link = form['action']
            return link
        except KeyError:
            return None
    return None

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

def send_post_request(url, params={}, headers={}):
    '''
    Attempts to open the link using a post request with the passed dictionary of
    params.

    TODO: Document exceptions.
    '''
    post_data_encoded = urllib.urlencode(params)
    request = urllib2.Request(url, post_data_encoded, HTTP_HEADERS)
    for k in headers.keys():
        request.add_header(k, headers[k])
    return urllib2.urlopen(request)

def unwrap_html_contents(elmnt):
    '''
    Recursively tries to unwrap the data from within an element until there are
    no more layers to unwrap.  This shouldn't run into any infinite loops
    as eventually an element will be empty or will contain some sort of
    contents.

    This will return the first non-None object it sees, so this is more for
    taking elements out of nested tags, like:

    <tt>
        <a>
            <i>
                <strong>
                    Foober Bazzle-Snazz
                </string>
            </i>
        </a>
    </tt>

    Which would be a pain to hard code.
    '''
    contents = elmnt.contents
    while contents:
        for c in contents:
            if c.string is None:
                return unwrap_html_contents(c)
            else:
                return c.string
    return None

def parse_table_headers(tags, html_str):
    '''
    This is for getting the data directly under the set of table headers on a
    page (for now).  By that I mean if a table passed was rendered such as this:

     _____ _____
    | Foo | Bar |
     ----- -----
    | 22  | 64  |
     ----- -----

    Then the data under 'Foo' would be 22, and the data under 'Bar' would be 64.

    The arguments required are a list of table header names (case insensitive) 
    that the callee intends to find in at most one of the table headers (the 
    last matching table header will have its value stored in the dictionary for
    now).

    For example, if we simply want the data under the headers 'Foo' and 'Bar,'
    we would pass ['Foo', 'Bar'] as the first parameter, and then if 'Foo' and
    'Bar' were found anywhere within the table headers of the html string that
    renders the example above, then as long as said value is not None, the value
    of the corresponding string that led to the match will be a key within the
    returned dictionary, with the value as the string directly below the header.

    From the above example, calling parse_table_headers(['Foo', 'Bar'], html),
    where html would render something similar to the above, the returned
    dictionary would be:

    { u'Foo': u'22', u'Bar': u'64' }
    '''

    regex = re.compile(
        "^.*(?P<header>{0})".format('|'.join(tags)),
        re.IGNORECASE,
    )
    page = BeautifulSoup(html_str, convertEntities=BeautifulSoup.HTML_ENTITIES)
    # Remove all <br /> tags, because they'll only screw things up.
    for br in page.findAll('br'):
        br.extract()
    # This is a bit of a hack, butif we parse the page again, all the removed br
    # tags will leave contiguous strings in their wake.  This will allow us to
    # parse things like the current enrollment and room capacity.
    page = BeautifulSoup(str(page))
    info = {}

    # Go through the tables and find any class info (this loop is why I hate
    # tables....).  We'll iterate through all of the rows and columns, keeping
    # track of where we are so we can access other sections of the rows and
    # columns if we encounter the types of elements we're looking for.
    tables = page.findAll('table')  
    for table in tables:
        rows = table.findAll('tr')
        row_index = 0
        for row in rows:
            headers = row.findAll('th')
            column_index = 0
            for header in headers:
                # This will only match after converting the unicode to a regular
                # string.  There's likely a far better way to do this.
                m = re.match(regex, str(header.string))

                '''
                If m was a match, then we'll simply pluck the element directly
                under the row and column we were looking for.  After that, if
                the element under the header is not None, then we have a key and
                value that can be stored in the info dictionary.
                '''
                if m is not None:
                    next_row_elmnt = rows[
                        row_index + 1
                    ].findAll('td')[column_index]
                    string = unwrap_html_contents(next_row_elmnt)
                    if string is not None:
                        info[m.group('header')] = string.strip()
                column_index += 1
            row_index += 1
    return info
