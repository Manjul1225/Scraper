import time
import copypaste
import sys
import re
import traceback
from selenium import webdriver
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, \
    TimeoutException, ElementClickInterceptedException, ElementNotInteractableException, \
    JavascriptException, StaleElementReferenceException



children = set()
childrens_children = {}
types = {}
parent_types = {}
parent_types_list = []
ignore = []
file_string = ''
devices_file_given = False
parents = ['WS-C3850-48T-L','WS-C3850-48T-S']
parents_for_output = set()
types_for_output = set()
all_parents_for_output = set()
all_types_for_output = set()

if len(sys.argv) > 1:
    arg = sys.argv[1]
    #process the devices file if given
    if arg.endswith('.txt') or arg.endswith('.csv'):
        devices_file_given = True
        f = open(arg, 'r')
        file_string = f.read()
        f.seek(0)
        read = f.readlines()
        f.close()
        parents = []

        for i in read:
            splited = i.split(':')[:2]

            if splited[0] not in parent_types:
                parent_types[splited[0]] = []
                parent_types_list.append(splited[0])
            parent_types[splited[0]].append(splited[1].replace('\r', '').replace('\n', ''))

            if ':SUCCESS' in i or ':NOTFOUND' in i:
                continue
            elif ':FAILED' in i:
                parents.append(i.split(':')[1].replace('\r', '').replace('\n', ''))
            else:
                parents.append(i.split(':')[1].replace('\r', '').replace('\n', ''))
    else:
        parents = [arg]

if len(sys.argv) > 2:
    #process the ignore list if given
    ignore_file = open(sys.argv[2])
    ignore_list = ignore_file.readlines()
    ignore_file.close()

    for i in ignore_list:
        ignore.append(i.replace('\r', '').replace('\n', ''))


#recursively walk through device's tree
def get_childrens_children(level):
    labels = driver.find_elements_by_css_selector('tr.majorProductList.highlightedRow')
    skutitle = True
    if len(labels) == 0:
        labels = driver.find_elements_by_css_selector(
            'td.icwFirst.width35p > div.floatLeft.marginR7')
        skutitle = False

    for a in range(len(labels)):
        if skutitle:
            try:
                title = ''
                try:
                    title = driver.find_elements_by_css_selector('span.skutitle')[a].text
                except IndexError:
                    a = 0
                    title = driver.find_elements_by_css_selector('span.skutitle')[a].text
                except StaleElementReferenceException:
                    driver.execute_script(
                        'document.querySelectorAll("span.skutitle")[{}].scrollIntoView()'.format(a))
                    title = driver.find_elements_by_css_selector('span.skutitle')[a].text
                if ignore:
                    is_in_ignore = check_with_regex(title, ignore)
                    if is_in_ignore:
                        if level > 0:
                            save_childrens_children()
                        continue
                if title not in label_names:
                    label_names.append(title)
                else:
                    continue
                driver.execute_script(
                    'document.querySelectorAll("tr.majorProductList.highlightedRow ' +
                    'td label.label_radio")[{}].click()'.format(a))
            except JavascriptException:
                try:
                    driver.execute_script(
                        'document.getElementsByClassName("label_check")[{}].click()'.format(a))
                except JavascriptException: 
                    a = 0
                    driver.execute_script(
                        'document.querySelectorAll(".label_radio.r_off")[{}].click()'.format(a))
        else:
            title = driver.find_elements_by_css_selector('td.icwFirst.width35p > ' +
                'div.floatLeft.marginR7')[a].text
            if ignore:
                is_in_ignore = check_with_regex(title, ignore)
                if is_in_ignore:
                    if level > 0:
                        save_childrens_children()
                    continue
            if title not in label_names:
                label_names.append(title)
            else:
                continue
            driver.execute_script(
                'document.querySelectorAll("td.icwFirst.width35p > ' +
                'div.width30px.footerLeft > label")[{}].click()'.format(a))

        wait_preloader_disappearing(driver.find_element_by_id('preloader'))

        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'tr.majorProductList.highlightedRow'))
            )
        except TimeoutException:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'td.icwFirst.width35p > div.floatLeft.marginR7'))
            )

        if level > 0:
            save_childrens_children()

        elems = driver.find_elements_by_css_selector('span.sku.tooltip > a')
        if len(elems) > 0:
            t = elems[-1].text
            if Elemtext.elem_text == t or t == '':
                clear_selection(skutitle)
                continue
            elems[-1].click()
            Elemtext.elem_text = t
        else:
            clear_selection(skutitle)
            continue

        categories = driver.find_elements_by_class_name('categoryChange ')
        if len(categories) > 1:
            save_childrens_children()
            get_childrens_children(level=level)
            for c in range(len(categories)):
                try:
                    driver.find_element_by_id('backToTop').click()
                except (ElementClickInterceptedException, ElementNotInteractableException) as e:
                    pass
                driver.execute_script(
                    "document.getElementsByClassName('categoryChange ')[{}].click()".format(c))         
                save_childrens_children()
                get_childrens_children(level=level)

        get_childrens_children(level=level+1)

        try:
            driver.find_element_by_id('backToTop').click()
        except (ElementClickInterceptedException, ElementNotInteractableException) as e:
            pass

        try:
            driver.execute_script(
                "document.querySelector('a.breadCrumbList.renderNewClass:last-child').click()")
        except JavascriptException:
            pass
        clear_selection(skutitle)


#deselect all selected devices
def clear_selection(sktitle):
    try:
        disabled = driver.find_elements_by_class_name('c_dis')
        while True:
            driver.execute_script(
                "document.querySelector('label.label_check.c_on:not(.c_dis)').click()")
            if disabled:
                time.sleep(1)
            wait_preloader_disappearing(driver.find_element_by_id('preloader'))
    except JavascriptException:
        if sktitle:
            try:
                last = driver.find_elements_by_css_selector("tr.majorProductList" +
                            ".highlightedRow td label.label_radio")[-1]
                checked = driver.find_element_by_css_selector("tr.majorProductList" +
                            ".highlightedRow td label.label_radio.r_on")
                if last == checked:
                    try:
                        driver.find_element_by_css_selector('span.clearSelectionDiv > span > a').click()
                    except ElementNotInteractableException:
                        pass
            except (NoSuchElementException, IndexError) as e:
                pass
        else:
            pass

    wait_preloader_disappearing(driver.find_element_by_id('preloader'))


def get_selected_category():
    selected_category = ''
    try:
        selected_category = driver.find_element_by_class_name('selectedCtegory').text
    except NoSuchElementException:
        try:
            selected_category = driver.find_element_by_class_name('categoryChange').text
        except NoSuchElementException:
            selected_category = driver.find_element_by_css_selector('#breadCrumb > strong').text

    return selected_category


def save_childrens_children():
    selected = driver.find_element_by_css_selector('a.marginR3.Select').text
    selected_category = get_selected_category()

    if selected not in childrens_children:
        childrens_children[selected] = set()
    if selected_category not in types:
        types[selected_category] = set()

    ch_elems = driver.find_elements_by_class_name('skutitle') 
    if len(ch_elems) == 0:
        ch_elems = driver.find_elements_by_css_selector(
            'td.icwFirst.width35p > div.floatLeft.marginR7')

    for ch in ch_elems:
        childrens_children[selected].add(ch.text)
        types[selected_category].add(ch.text)


def save_children_and_types():
    selected_category = get_selected_category()

    types[selected_category] = set()
    children_elems = ''

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'skutitle'))
        )
        children_elems = driver.find_elements_by_class_name('skutitle')
    except TimeoutException:
        children_elems = driver.find_elements_by_class_name('productSKU')

    for child in children_elems:
        children.add(child.text)
        types[selected_category].add(child.text)


def wait_preloader_disappearing(element):
    while(True):
        try:
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException) as e:
            break
        time.sleep(0.1)


#check if device is in the ignore file
def check_with_regex(string, ignore):
    for igno in ignore:
        if re.match(igno, string):
            return True
    return False


class Elemtext:
    elem_text = ''


driver = webdriver.Firefox()
devices_file = ''
if devices_file_given:
    devices_file = open(sys.argv[1], 'w')


for parent in parents:
    types_for_output.add(
        '{"type":"%s","items":%s}' % (
            parent_types_list[-1], json.dumps(list(parent_types[parent_types_list[-1]]))))
    try:
        label_names = []
        driver.get('https://apps.cisco.com/ccw/cpc/guest/estimate/create')

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'fancybox-wrap'))
            )
            driver.find_element_by_id('estimateCartConfirmationcontinueBth').click()
        except:
            pass

        add_item = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'searchProd'))
        )

        wait_preloader_disappearing(driver.find_element_by_class_name('preloaderOverlay'))
        wait_preloader_disappearing(driver.find_element_by_id('fancybox-overlay'))

        add_item.click()
        add_item.send_keys(parent)

        driver.execute_script("document.getElementsByClassName('preloaderOverlay')[0].remove()")
        driver.find_element_by_id('addProduct').click()

        select_options = ''
        try:
            select_options = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, '.actionButtons > ul > li:nth-child(3)'))
            )
        except TimeoutException:
            if devices_file_given:
                if file_string.split(parent)[1].startswith(':FAILED'):
                    file_string = file_string.replace(parent+':FAILED', parent + ':NOTFOUND', 1)
                else:
                    file_string = file_string.replace(parent, parent + ':NOTFOUND', 1)
            continue

        if select_options.text != 'Select Options' and select_options.text != 'Edit Options':
            if devices_file_given:
                if file_string.split(parent)[1].startswith(':FAILED'):
                    file_string = file_string.replace(parent+':FAILED', parent + ':SUCCESS', 1)
                else:
                    file_string = file_string.replace(parent, parent + ':SUCESS', 1)
            continue
        select_options.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'skutitle'))
        )

        types_list = driver.find_elements_by_css_selector('a.renderNewClass:not(.sku)')

        # scrape children and types
        for n in range(len(types_list)):
            
            driver.execute_script(
                "document.querySelectorAll('div.arwOvrLapFix > " +
                "a.renderNewClass.marginR3')[{}].click()".format(n))

            save_children_and_types()
            get_childrens_children(level=0)

            categories = driver.find_elements_by_class_name('categoryChange ')
            if len(categories) > 1:

                for c in range(len(categories)):
                    try:
                        driver.find_element_by_id('backToTop').click()
                    except (ElementClickInterceptedException, ElementNotInteractableException) as e:
                        pass

                    driver.execute_script(
                        "document.getElementsByClassName('categoryChange ')[{}].click()".format(c))         

                    save_children_and_types()
                    get_childrens_children(level=0)


        parents_for_output.add(
            '{"parent":"%s","children":%s}' % 
            (parent, str(json.dumps(list(children))).replace('{', '').replace('}', '')))

        for i in childrens_children:
            parents_for_output.add(
                '{"parent":"%s","children":%s}' % (i, json.dumps(list(childrens_children[i]))))

        for i in types:
            types_for_output.add('{"type":"%s","items":%s}' % (i, json.dumps(list(types[i]))))

        final_json = '{"parents":%s, "types":%s}' % (list(parents_for_output), 
                                                       list(types_for_output))
        final_json = final_json.replace("'", "").replace('\\', '')

        print(final_json)
        print('')
        print('')
        copypaste.copy(final_json)

        for i in parents_for_output:
            all_parents_for_output.add(i)
        for i in types_for_output:
            all_types_for_output.add(i)
        
        parents_for_output = set()
        types_for_output = set()

        for i in types:
            for x in types[i]:
                ignore.append(x)

        children = set()
        childrens_children = {}
        types = {}

        if devices_file_given:
            if file_string.split(parent)[1].startswith(':FAILED'):
                file_string = file_string.replace(parent+':FAILED', parent + ':SUCCESS', 1)
            else:
                file_string = file_string.replace(parent, parent + ':SUCCESS', 1)

    except KeyboardInterrupt:
        break
    except:
        etype, value, tb = sys.exc_info()
        print ('=========================================')
        print (parent)
        traceback.print_exception(etype, value, tb)
        print ('=========================================')

        if devices_file_given:
            if file_string.split(parent)[1].startswith(':FAILED'):
                pass
            else:
                file_string = file_string.replace(parent, parent + ':FAILED', 1)
            continue


if devices_file_given:
    devices_file.write(file_string)
    devices_file.close()

for i in parent_types:
    all_types_for_output.add('{"type":"%s","items":%s}' % (i, json.dumps(list(parent_types[i]))))

final_json = '{"parents":%s, "types":%s}' % (list(all_parents_for_output), 
                                               list(all_types_for_output))
final_json = final_json.replace("'", "").replace('\\', '')
copypaste.copy(final_json)

driver.close()
