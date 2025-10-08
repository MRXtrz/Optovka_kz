import time
import logging
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class CustomSeleniumMiddleware:
    def __init__(self, chromedriver_path, headless=True, window_size=(1920,1080)):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)

    @classmethod
    def from_crawler(cls, crawler):
        chromedriver_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        headless = crawler.settings.getbool('SELENIUM_HEADLESS', True)
        window_size = crawler.settings.get('SELENIUM_WINDOW_SIZE', (1920,1080))
        mw = cls(chromedriver_path=chromedriver_path, headless=headless, window_size=window_size)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        return mw

    def process_request(self, request, spider):
        if not request.meta.get('selenium'):
            return None
        url = request.url
        logger.debug(f"Selenium rendering: {url}")
        self.driver.get(url)
        time.sleep(request.meta.get('selenium_wait', 1))
        body = str.encode(self.driver.page_source)
        return HtmlResponse(self.driver.current_url, body=body, encoding='utf-8', request=request)

    def spider_closed(self, spider):
        try:
            self.driver.quit()
        except Exception:
            pass
