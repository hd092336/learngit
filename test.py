from sys import exit
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException


def is_element_exist(driver, locate):
    try:
        driver.find_element(*locate)
        return True
    except NoSuchElementException:
        return False


def login(driver, un, pwd):
    # login to ABS system
    driver.find_element(By.XPATH, "//input[@ng-model='userName']").send_keys(un)
    driver.find_element(By.XPATH, "//input[@ng-model='password']").send_keys(pwd)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    sleep(1)


def select_established_product_list(driver):
    # 存续期管理 -> 已成立产品列表
    driver.find_element(By.XPATH, "//li[@ng-repeat='menu in menus'][3]").click()
    driver.find_element(By.XPATH, "//a[contains(@ui-sref, 'establishedProductList')]").click()
    sleep(2)


def select_product(driver, product_name, product_type, is_circular_buying):
    # 已成立产品列表中选择产品
    product_name_selector = driver.find_element(By.ID, "productName")
    Select(product_name_selector).select_by_visible_text(product_name)  # select product name
    product_type_selector = driver.find_element(By.ID, "productType")
    Select(product_type_selector).select_by_visible_text(product_type)  # select product type
    is_circular_selector = driver.find_element(By.ID, "isCircularBuying")
    Select(is_circular_selector).select_by_value(is_circular_buying)  # 是否循环购买，1：是，0：否
    driver.find_element(By.XPATH, "//button[contains(text(),'查询')]").click()
    try:
        driver.find_element(By.LINK_TEXT, product_name).click()
        sleep(2)
    except NoSuchElementException:
        circular_buying_str = "循环" if int(is_circular_buying) else "非循环"
        print("%s不是一个%s, %s产品。" % (product_name, product_type, circular_buying_str))
        exit(-1)


def get_payment_and_status(driver):
    plan = {}
    status = {}
    driver.find_element(By.XPATH, "//li[@heading='现金流分配']/a").click()
    driver.find_element(By.XPATH, "//button[contains(text(),'修改兑付计划')]").click()
    sleep(1)
    for record in driver.find_elements(By.XPATH, "//tbody/tr"):
        record_str = record.text
        cashinflow_date, status1, cashoutflow_date, status2 = record_str.split(" ")
        plan[cashinflow_date] = cashoutflow_date
        status[cashinflow_date] = status1
        status[cashoutflow_date] = status2
    return plan, status


def batch_confirm(driver):
    cash_in_flows = driver.find_elements(By.XPATH, "//tbody[@id='tbodyId']/tr")
    cash_in_flow_number = len(cash_in_flows)
    if cash_in_flow_number == 0:
        print("现金流入计划：%s中无未确认记录。" % cash_in_flow_date)
    else:
        for record in range(1, cash_in_flow_number + 1):
            xpath_of_cashInflow = "//tbody[@id='tbodyId']/tr[%d]" % record
            cashInflowDate = driver.find_element(By.XPATH, "%s/td[6]" % xpath_of_cashInflow).text
            driver.find_element(By.ID, "paidDate%d" % (record - 1)).send_keys(cashInflowDate, Keys.ENTER)
        all_check_button = driver.find_element(By.ID, "allCheck")
        driver.execute_script("arguments[0].scrollIntoView(false);", all_check_button)
        driver.find_element(By.ID, "allCheck").click()
        while is_element_exist(driver, (By.XPATH, "//div[@id='toast-container']/child::*")):
            sleep(0.5)  # 等待，以防警告信息遮挡页面按钮
        driver.find_element(By.XPATH, "//button[contains(text(),'批量确认返本付息')]").click()
        driver.find_element(By.XPATH, "//button[@ng-click='ok()']").click()
        sleep(2)


def confirm_asset_cash_info(driver):
    pages = driver.find_elements(By.XPATH, "//ul[@class='pagination']//a")
    page_number = len(pages) if len(pages) else 1
    for page in range(1, page_number + 1):
        if page == 1:
            batch_confirm(driver)
        else:
            pages[page].click()
            sleep(2)
            batch_confirm(driver)


def confirm_return_principal_and_interest(driver, date):
    driver.find_element(By.XPATH, "//li[@heading='返本付息']/a").click()  # 选择返本付息
    asset_status_selector = driver.find_element(By.ID, "productStatus")
    Select(asset_status_selector).select_by_value("0")  # select asset status, 0：未确认, 1：已确认
    driver.find_element(By.XPATH, "//ul[@id='cashInfoDate']//button").click()
    driver.find_element(By.XPATH, "//li[contains(@ng-repeat,'cashInflowDate')]/a[text()='%s']" % date).click()
    driver.find_element(By.XPATH, "//button[@ng-click='queryCashFlowInfo()']").click()  # 查询
    confirm_asset_cash_info(driver)


def confirm_cash_in_flow_summary(driver, date):
    # 进入现金流流入页面
    driver.find_element(By.XPATH, "//li[@heading='现金流流入']/a").click()
    driver.find_element(By.XPATH, "//button[contains(text(),'现金流汇总')]").click()
    # 确认现金流汇总
    try:
        xpath_of_summary = "//tr[contains(@ng-repeat,'summaryTable')][td[text()='%s']]" % date
        driver.find_element(By.XPATH, "%s//button[@confirm='确定要确认吗?']" % xpath_of_summary).click()
        driver.find_element(By.XPATH, "//button[@ng-click='ok()']").click()
        sleep(2)
    except NoSuchElementException:
        print("现金流计划：%s已确认" % date)


abs_url = 'http://qa-abs.xyams.com'
username = "gaoyi"
password = "000000"
test_product_name = "ABS_AT_02"
# test_product_name = "www"

options = webdriver.ChromeOptions()
# ownload.default_directory：设置下载路径
# profile.default_content_settings.popups：设置为 0 禁止弹出窗口
prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': 'd:\\'}
options.add_experimental_option('prefs', prefs)

dr = webdriver.Chrome(chrome_options=options)
dr.implicitly_wait(5)  # wait for no more than 5s
dr.maximize_window()
dr.get(abs_url)

try:
    # 登录ABS系统
    login(dr, username, password)
    # 存续期管理 -> 已成立产品列表
    select_established_product_list(dr)
    # 已成立产品列表中选择ABS非循环产品
    select_product(dr, test_product_name, "ABS项目", "0")
    dr.find_element(By.XPATH, "//li[@heading='返本付息']/a").click()  # 选择返本付息
    dr.find_element(By.XPATH, "//ul[@id='cashInfoDate']//button").click()
    dr.find_element(By.XPATH, "//button[@ng-click='queryCashFlowInfo()']").click()  # 查询
    pages = dr.find_elements(By.XPATH, "//ul[@class='pagination ']//a")
    page_number = len(pages) if len(pages) else 1
    for page in range(1, page_number + 1):
        if page == 1:
            print("Page 1 is OK.")
        else:
            dr.find_element(By.XPATH, "//ul[@class='pagination ']//a[text()=%d]" % page).click()
            print("Page %d is OK." % page)
        sleep(2)
except Exception as e:
    print("Exception found", e)
finally:
    dr.quit()
