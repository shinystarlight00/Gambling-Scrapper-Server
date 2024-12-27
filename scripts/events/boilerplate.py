import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

import db
import requests
import traceback
from time import sleep
from helpers import Helpers
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class EventBoilerplate:

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    
    def __init__(self, driver, name):
        load_dotenv(dotenv_path=os.path.join(self.BASEDIR, '../../.env'), override=True)

        self.node_env = os.getenv("NODE_ENV")
        self.flask_server = os.getenv("FLASK_SERVER")
        self.twocaptcha_api = os.getenv("2CAPTCHA")

        self.name = name
        self.prefix = name + " "
        self.driver = driver
        self.helpers = Helpers()
        self.db = db.DB(name.lower())
        self.wait = WebDriverWait(driver, 15)

    ## Methods to reach elements from driver
    def get_elements(self, selector, delay = 15):
        try:
            if delay == 0: return self.driver.find_elements(By.CSS_SELECTOR, selector)
            return self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
        except: pass

    def get_element(self, selector):
        try:
            return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except: pass

    def get_innerText(self, selector):
        try:
            return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).get_attribute("innerText")
        except: return ""

    def get_element_attribute(self, selector, attribute):
        try:
            return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).get_attribute(attribute)
        except: return False

    ## Methods to reach element inside element
    def get_from_elements(self, el, selector, delay = 30):
        try:
            if delay == 0: return el.find_elements(By.CSS_SELECTOR, selector)
            return WebDriverWait(el, delay).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
        except: pass

    def get_from_element(self, el, selector, delay = 30):
        try:
            if delay == 0: return el.find_element(By.CSS_SELECTOR, selector)
            return WebDriverWait(el, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except: pass

    def get_from_innerText(self, el, selector, delay = 30):
        try:
            if delay == 0: return el.find_element(By.CSS_SELECTOR, selector).get_attribute("innerText")
            return WebDriverWait(el, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).get_attribute("innerText")
        except: return ""

    def get_from_element_attribute(self, el, selector, attribute, delay = 30):
        try:
            if delay == 0: return el.find_element(By.CSS_SELECTOR, selector).get_attribute(attribute)
            return WebDriverWait(el, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).get_attribute(attribute)
        except: return ""

    ## Cloudflare Bypass
    def bypass_cloudflare(self, driver):
        try:
            sleep(20)

            while True:
                # Check if Cloudflare Exists
                footer_text = self.get_innerText("#footer-text")
                if (not footer_text) or ("Cloudflare" not in footer_text):
                    print("Cloudflare is not detected")
                    return True

                print("Cloudflare Bypass")

                # Inject script
                driver.execute_script("location.reload();")

                try:
                    turnsite = driver.execute_async_script("""
                        const done = arguments[arguments.length - 1];
                        const i = setInterval(() => {
                            if (window?.turnstile) {
                                clearInterval(i)
                                window.turnstile.render = (a,b) => {
                                    let p = {
                                        type: "TurnstileTaskProxyless",
                                        websiteKey: b.sitekey,
                                        websiteURL: window.location.href,
                                        data: b.cData,
                                        pagedata: b.chlPageData,
                                        action: b.action,
                                        userAgent: navigator.userAgent
                                    };
                                    window.tsCallback = b.callback;
                                    done(p);
                                    console.log(p);
                                }
                            }
                        }, 1)
                    """)
                except:
                    print("Retrying CF Bypass...")
                    continue

                if not turnsite["data"]:
                    print("Retrying CF Bypass...")
                    continue

                request = {
                    "key": self.twocaptcha_api,
                    "method": "turnstile",
                    "type": "TurnstileTaskProxyless",
                    "pageurl": turnsite["websiteURL"],
                    "sitekey": turnsite["websiteKey"],
                    "action": "managed",
                    "data": turnsite["data"],
                    "pagedata": turnsite["pagedata"],
                    "useragent": turnsite["userAgent"],
                    "json": 1
                }

                task_response = requests.post(url="https://2captcha.com/in.php", json=request)
                task_response = task_response.json()

                print(task_response)

                if task_response["status"] != 1:
                    print(task_response)
                    print("2Captcha in.php failed")
                    return False

                success = False

                while True:
                    sleep(15)

                    listener_response = requests.get(
                        url="https://2captcha.com/res.php?key={}&action=get&id={}&json=1".format(
                            self.twocaptcha_api,
                            task_response["request"]
                        )
                    ).json()

                    if listener_response["status"] == 1:
                        print("\n{}\n".format(listener_response["request"]))
                        success = True
                        break
                    else:
                        print(listener_response)

                        if listener_response["request"] == "ERROR_CAPTCHA_UNSOLVABLE":
                            break

                if success:
                    # Solve the captcha
                    driver.execute_script("window.tsCallback('{}')".format(listener_response["request"]))
                    return True

        except:
            print(traceback.format_exc())