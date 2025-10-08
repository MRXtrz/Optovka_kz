BOT_NAME = 'parser_service'
SPIDER_MODULES = ['parser_service.spiders']
NEWSPIDER_MODULE = 'parser_service.spiders'

DOWNLOADER_MIDDLEWARES = {
    'parser_service.middlewares.CustomSeleniumMiddleware': 800,
}

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = '/usr/bin/chromedriver'
SELENIUM_HEADLESS = True
SELENIUM_WINDOW_SIZE = (1920, 1080)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 2

LOG_LEVEL = 'INFO'
LOG_FILE = 'spider.log'
DUPEFILTER_DEBUG = True
