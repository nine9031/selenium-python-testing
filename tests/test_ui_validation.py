"""Member 2 UI & Validation; mapped to FT-VAL-02 through FT-VAL-10."""
import json
import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def element(driver, id):
    return driver.find_element(By.ID, id)


def enter(driver, id, value):
    field = element(driver, id)
    field.clear()
    if value:
        field.send_keys(value)


def fill(driver, name='Test-Pet-UI', weight='10', pet_type='dog', activity='medium'):
    enter(driver, 'pet-name', name)
    enter(driver, 'pet-weight', weight)
    Select(element(driver, 'pet-type')).select_by_value(pet_type)
    Select(element(driver, 'pet-activity')).select_by_value(activity)


def posts(driver):
    return driver.execute_script('''return window.testRequests.filter(
        x => x.method.toUpperCase() === 'POST' && new URL(x.url, location.href).pathname === '/api/pets');''')


def error(driver, id):
    field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, id)))
    assert field.text.strip(), f'{id}: error message is empty'
    rgb = [int(n) for n in re.findall(r'\d+', field.value_of_css_property('color'))[:3]]
    assert len(rgb) == 3 and rgb[0] > rgb[1] and rgb[0] > rgb[2], f'{id}: message must be red'
    return field


def submit(driver):
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btn-submit')))
    driver.execute_script('arguments[0].scrollIntoView({block:"center"})', button)
    button.click()


def saved_row(driver, name):
    def matching(d):
        for row in d.find_elements(By.CSS_SELECTOR, '#pets-table-body tr'):
            if row.find_element(By.TAG_NAME, 'td').text == name:
                return row
        return False
    return WebDriverWait(driver, 15).until(matching)


def assert_preview(driver, id, expected, unit):
    text = element(driver, id).text
    number, actual_unit = text.rsplit(' ', 1)
    assert actual_unit == unit
    assert float(number.replace(',', '')) == pytest.approx(expected)


def test_ft_val_02_empty_form(driver):
    """All four required fields show red errors; no save request."""
    submit(driver)
    for id in ['error-name', 'error-type', 'error-weight', 'error-activity']:
        error(driver, id)
    assert posts(driver) == []


@pytest.mark.parametrize('name', ['', '   '], ids=['empty', 'spaces'])
def test_ft_val_03_blank_name(driver, name):
    fill(driver, name=name)
    submit(driver)
    error(driver, 'error-name')
    assert posts(driver) == []


@pytest.mark.parametrize('text', ['abc', '10abc'])
@pytest.mark.parametrize('method', ['typing', 'bulk-insert'])
def test_ft_val_04_non_numeric_weight(driver, pet_name, text, method):
    fill(driver, name=pet_name, weight='')
    field = element(driver, 'pet-weight')
    field.click()
    if method == 'typing':
        field.send_keys(text)
    else:
        # Bulk text insertion through the browser input engine, not assignment to .value.
        driver.execute_cdp_cmd('Input.insertText', {'text': text})
    actual = field.get_property('value')
    assert not any(c.isalpha() for c in actual), 'Letters must not remain in a numeric input'
    # Chrome rejects letters: abc leaves an empty field; 10abc leaves valid 10.
    expected = '' if text == 'abc' else '10'
    assert actual == expected, f'Expected filtered value {expected!r}, got {actual!r}'
    submit(driver)
    if expected == '':
        error(driver, 'error-weight')
        assert posts(driver) == [], 'An empty weight must not be saved'
    else:
        row = saved_row(driver, pet_name)
        requests = posts(driver)
        assert len(requests) == 1, 'Expected exactly one save request'
        assert json.loads(requests[0]['body'])['weight'] == 10
        weight_cell = row.find_elements(By.TAG_NAME, 'td')[2].text
        assert float(weight_cell.replace('kg', '').replace(',', '').strip()) == 10
        assert not element(driver, 'error-weight').is_displayed()


@pytest.mark.parametrize('weight', ['', '0', '-5'], ids=['empty', 'zero', 'negative'])
def test_ft_val_05_invalid_weight(driver, weight):
    fill(driver, weight=weight)
    submit(driver)
    error(driver, 'error-weight')
    assert not element(driver, 'preview-box').is_displayed()
    assert posts(driver) == []


def test_ft_val_06_dog_weight_below_minimum(driver, pet_name):
    """Dog weight must be within 0.5 to 100 kg; 0.1 must not be saved."""
    fill(driver, name=pet_name, weight='0.1', pet_type='dog')
    assert float(element(driver, 'pet-weight').get_property('value')) == 0.1
    submit(driver)
    message = error(driver, 'error-weight')
    assert '0.5' in message.text and '100' in message.text, (
        'Expected the dog weight range 0.5 - 100 kg in the warning'
    )
    assert posts(driver) == [], 'Dog weight 0.1 kg must not be sent for saving'
    assert all(
        row.find_element(By.TAG_NAME, 'td').text != pet_name
        for row in driver.find_elements(By.CSS_SELECTOR, '#pets-table-body tr')
    ), 'Rejected weight must not create a history row'


@pytest.mark.parametrize('weight', ['2.5', '10'])
def test_ft_val_06_valid_weight(driver, pet_name, weight):
    fill(driver, name=pet_name, weight=weight)
    assert float(element(driver, 'pet-weight').get_property('value')) == float(weight)
    assert element(driver, 'preview-box').is_displayed()
    submit(driver)
    saved_row(driver, pet_name)
    assert len(posts(driver)) == 1
    assert not element(driver, 'error-weight').is_displayed()


@pytest.mark.parametrize('missing,error_id', [('pet-type', 'error-type'), ('pet-activity', 'error-activity')])
def test_ft_val_07_missing_selection(driver, missing, error_id):
    fill(driver)
    Select(element(driver, missing)).select_by_value('')
    submit(driver)
    error(driver, error_id)
    assert posts(driver) == []


@pytest.mark.parametrize('pet_type', ['dog', 'cat'])
@pytest.mark.parametrize('activity', ['low', 'medium', 'high'])
def test_ft_val_07_valid_selections(driver, pet_name, pet_type, activity):
    fill(driver, name=pet_name, pet_type=pet_type, activity=activity)
    assert Select(element(driver, 'pet-type')).first_selected_option.get_attribute('value') == pet_type
    assert Select(element(driver, 'pet-activity')).first_selected_option.get_attribute('value') == activity
    submit(driver)
    saved_row(driver, pet_name)
    assert len(posts(driver)) == 1


def test_ft_val_08_correct_errors_and_save(driver, pet_name):
    submit(driver)
    error(driver, 'error-name')
    error(driver, 'error-weight')
    enter(driver, 'pet-name', pet_name)
    assert not element(driver, 'error-name').is_displayed()
    assert element(driver, 'error-weight').is_displayed()
    fill(driver, name=pet_name, weight='2.5', pet_type='cat', activity='low')
    submit(driver)
    saved_row(driver, pet_name)
    for id in ['error-name', 'error-type', 'error-weight', 'error-activity']:
        assert not element(driver, id).is_displayed()


def test_ft_val_09_layout_and_live_preview(driver):
    for id in ['pet-name', 'pet-type', 'pet-weight', 'pet-activity', 'btn-submit',
               'summary-total-pets', 'summary-total-water', 'summary-total-food']:
        assert element(driver, id).is_displayed()
    fill(driver)
    assert_preview(driver, 'preview-water', 600, 'ml')
    assert_preview(driver, 'preview-food', 216, 'g')
    Select(element(driver, 'pet-activity')).select_by_value('high')
    assert_preview(driver, 'preview-water', 600, 'ml')
    assert_preview(driver, 'preview-food', 252, 'g')
    assert posts(driver) == [], 'Preview must update without saving'


@pytest.mark.parametrize('width,height', [(375, 812), (1366, 768)])
def test_ft_val_10_responsive(driver, pet_name, width, height):
    # Set actual viewport size, since OS window decorations vary across systems.
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': width < 600})
    for id in ['pet-name', 'pet-type', 'pet-weight', 'pet-activity', 'btn-submit']:
        field = element(driver, id)
        assert field.is_displayed() and field.is_enabled()
        rect = driver.execute_script('const r=arguments[0].getBoundingClientRect();return {left:r.left,right:r.right}', field)
        assert rect['left'] >= -1 and rect['right'] <= width + 1, f'{id} is clipped horizontally'
    fill(driver, name=pet_name, weight='0')
    submit(driver)
    message = error(driver, 'error-weight')
    assert message.size['height'] > 0
    assert posts(driver) == []
    enter(driver, 'pet-weight', '10')
    submit(driver)
    row = saved_row(driver, pet_name)
    delete_button = row.find_element(By.CSS_SELECTOR, '.btn-delete')
    driver.execute_script('arguments[0].scrollIntoView({block:"center", inline:"center"})', delete_button)
    assert delete_button.is_displayed() and delete_button.is_enabled()
    assert driver.execute_script('return document.documentElement.scrollWidth <= innerWidth + 1'), 'Whole page overflows horizontally'
