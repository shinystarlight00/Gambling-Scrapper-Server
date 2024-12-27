import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../events'))

import psutil
import atexit
from threading import Thread
from selenium import webdriver
from selenium_stealth import stealth
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

# Events
import RustMagic_events

# Threading
class RustMagic:
    def __init__(self):
        ua = UserAgent()

        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("window-size=1920,1080")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--user-agent={}'.format(ua.chrome))
        chrome_options.add_experimental_option("detach", True)

        self.driver = webdriver.Chrome(
            service = ChromeService(ChromeDriverManager().install()),
            options = chrome_options
        )

        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        self.Processes = psutil.Process(self.driver.service.process.pid).children(recursive=True)

    def start(self):
        def go(type):
            self.Events = RustMagic_events.Events(self.driver)
            self.Events.matching_func(type)

        types = ["live"]
        threads = []

        for i in range(len(types)):
            t = Thread(target=go, args=(types[i],))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def atExit(self):
        print("Closing Chrome Process.")

        for process in self.Processes:
            try: process.kill()
            except: pass

if __name__ == "__main__":
    instance = RustMagic()
    atexit.register(instance.atExit)
    instance.start()