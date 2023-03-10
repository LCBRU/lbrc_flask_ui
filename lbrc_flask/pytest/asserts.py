import re
from urllib.parse import urlparse, parse_qs
from flask import url_for
from lbrc_flask.pytest.helpers import login
from flask_api import status
from lbrc_flask.url_helpers import update_querystring


def _assert_html_standards(soup):
    assert soup.html is not None
    assert soup.html["lang"] == "en"
    assert soup.head is not None
    assert (
        soup.find(
            lambda tag: tag.name == "meta"
            and tag.has_attr("charset")
            and tag["charset"] == "utf-8"
        )
        is not None
    )
    assert soup.title is not None
    assert soup.body is not None


def _assert_csrf_token(soup):
    assert (
        soup.find("input", {"name": "csrf_token"}, type="hidden", id="csrf_token") is not None
    )


def _assert_basic_navigation(soup, user):
    assert soup.nav is not None
    assert soup.nav.find("a", href="/") is not None
    assert soup.nav.find("a", string=user.full_name) is not None
    assert soup.nav.find("a", href="/change") is not None
    assert soup.nav.find("a", href="/logout") is not None


def assert__error__message(soup, message):
    errors = "\n".join([d.text for d in soup.find_all("div", "alert")])
    rx = re.compile(message, re.IGNORECASE)
    assert rx.search(errors) is not None


def assert__error__required_field(soup, field_name):
    assert__error__message(soup, "Error in the {} field - This field is required.".format(field_name))


def assert__redirect(response, endpoint=None, url=None, **kwargs):
    assert response.status_code == status.HTTP_302_FOUND

    if endpoint:
        if urlparse(response.location).netloc:
            url = url_for(endpoint, _external=True, **kwargs)
        else:
            url = url_for(endpoint, _external=False, **kwargs)

    if url:
        assert response.location == url


def assert__requires_login(client, url, post=False):
    if post:
        response = client.post(url)
    else:
        response = client.get(url)

    # This should be a call to assert__redirect, but
    # flask_login or flask_security is adding the
    # endpoint parameters as querystring arguments as well
    # as having them in the `next` parameter  
    assert response.status_code == status.HTTP_302_FOUND

    login_loc = urlparse(url_for('security.login', next=url))
    resp_loc = urlparse(response.location)

    print(f"{resp_loc.path=}, {login_loc.path=}")
    assert resp_loc.path == login_loc.path
    print(f"{parse_qs(resp_loc.query).get('next')=}, {parse_qs(login_loc.query).get('next')=}")
    assert parse_qs(resp_loc.query).get('next') == parse_qs(login_loc.query).get('next')


def assert__requires_role(client, url, post=False):
    if post:
        resp = client.post(url)
    else:
        resp = client.get(url)

    assert__redirect(resp, url='/')


def assert__search_html(soup, clear_url):
    assert soup.find('input', id="search") is not None
    assert soup.find('a', string="Clear Search", href=clear_url) is not None
    assert soup.find('button', type="submit", string="Search") is not None


def assert__select(soup, id, options):
    select = soup.find('select', id=id)
    assert select is not None

    for o in options:
        assert select.find('option', value=o[0], string=o[1])


def get_and_assert_standards(client, url, user, has_form=False, has_navigation=True):
    resp = client.get(url)

    _assert_html_standards(resp.soup)

    if has_navigation:
        _assert_basic_navigation(resp.soup, user)

    if has_form:
        _assert_csrf_token(resp.soup)

    return resp


def assert__page_navigation(client, endpoint, parameters, items, page_size=5, form=None):
    page_count = ((items - 1) // page_size) + 1

    if form is not None:
        form_fields = filter(lambda x: x.name not in ['page', 'csrf_token'] and x.data, form)
        params = {**parameters, **{f.name: f.data for f in form_fields}}
    else:
        params = {**parameters}

    url = url_for(endpoint, **params)

    if page_count > 1:
        assert__page_navigation__pages(url, client, page_count, form)
    else:
        resp = client.get(url)
        paginator = resp.soup.find('ul', 'pagination')
        assert paginator is None


def assert__page_navigation__pages(url, client, page_count, form):
    for current_page in range(1, page_count + 1):
        resp = client.get(update_querystring(url, {'page': current_page}))
        paginator = resp.soup.find('ul', 'pagination')

        assert__page_navigation__page(url, paginator, page_count, current_page)


def assert__page_navigation__page(url, paginator, page_count, current_page):
    assert paginator is not None

    assert__page_navigation__link_exists(paginator, 'Previous', url, current_page - 1, current_page, page_count)
    assert__page_navigation__link_exists(paginator, 'Next', url, current_page + 1, current_page, page_count)

    assert__page_navigation__link_exists(paginator, 1, url, 1, current_page, page_count)
    assert__page_navigation__link_exists(paginator, page_count, url, page_count, current_page, page_count)

    for page in range(max(current_page - 2, 2), min(current_page + 3, page_count - 1)):
        assert__page_navigation__link_exists(paginator, page, url, page, current_page, page_count)


def assert__page_navigation__link_exists(paginator, string, url, page, current_page, page_count):
    link = paginator.find('a', 'page-link', string=string)

    assert link is not None

    if 0 < page <= page_count and page != current_page:
        assert__urls_the_same(update_querystring(url, {'page': page}), link['href'])
    else:
        assert 'href' not in link

    if 0 < page <= page_count:
        assert 'disabled' not in link.parent['class']
    else:
        assert 'disabled' in link.parent['class']

    if page == current_page:
        assert 'active' in link.parent['class']
    else:
        assert 'active' not in link.parent['class']


def assert__urls_the_same(url1, url2):
    assert update_querystring(url1, {}) == update_querystring(url2, {})


def assert__flash_messages_contains_error(client):
    with client.session_transaction() as session:
        return dict(session['_flashes']).get('error') is not None
