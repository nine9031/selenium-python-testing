import json
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def pytest_addoption(parser):
    parser.addoption('--base-url', default='http://127.0.0.1:8100')
    parser.addoption('--headless', action='store_true')


def api(base, path, method='GET'):
    with urlopen(Request(base + path, method=method), timeout=10) as response:
        return json.load(response)


@pytest.fixture
def base_url(request):
    base = request.config.getoption('--base-url').rstrip('/')
    if urlparse(base).hostname not in {'localhost', '127.0.0.1', '::1'}:
        pytest.fail('Use a local test server; the suite creates and deletes its own test records.')
    try:
        assert api(base, '/api/pets')['success']
    except Exception as exc:
        pytest.fail(f'Test server is unavailable at {base}: {exc}')
    return base


@pytest.fixture(scope='session')
def browser_session(request):
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'eager'
    if request.config.getoption('--headless'):
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1000')
    browser = webdriver.Chrome(options=options)
    browser.set_script_timeout(15)
    browser.set_page_load_timeout(45)
    try:
        yield browser
    finally:
        browser.quit()


@pytest.fixture
def driver(request, base_url, browser_session):
    browser = browser_session
    request.node.browser = browser
    browser.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride', {})
    browser.set_window_size(1440, 1000)
    browser.get(base_url)
    WebDriverWait(browser, 15).until(
        lambda d: d.find_element(By.ID, 'btn-submit').is_displayed()
        and d.execute_script('return typeof Swal !== "undefined"'))
    # Observe real application fetch calls; do not replace validation or API responses.
    browser.execute_script('''
        window.testRequests = [];
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            window.testRequests.push({url: String(url), method: options.method || 'GET',
                                      body: options.body || null});
            return originalFetch.apply(this, arguments);
        };
    ''')
    yield browser


@pytest.fixture
def pet_name(base_url, driver):
    # Each test owns one UUID prefix; never delete unrelated records.
    prefix = 'Selenium-UI-' + uuid4().hex + '-'
    yield prefix
    try:
        for pet in api(base_url, '/api/pets')['data']:
            if pet['name'].startswith(prefix):
                api(base_url, '/api/pets/' + pet['id'], 'DELETE')
    except Exception as exc:
        pytest.fail(f'Could not clean up records with prefix {prefix}: {exc}')


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    browser = getattr(item, 'browser', None)
    if report.when == 'call' and report.failed and browser:
        folder = Path('test-results')
        folder.mkdir(exist_ok=True)
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', item.nodeid)
        try:
            browser.save_screenshot(str(folder / (name + '.png')))
            (folder / (name + '.html')).write_text(browser.page_source, encoding='utf-8')
        except Exception:
            pass  # The original test failure remains visible in the pytest report.
