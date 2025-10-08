# test_spider.py
import scrapy
from scrapy_selenium import SeleniumRequest
import json

class TestSpider(scrapy.Spider):
    name = "test1"
    allowed_domains = ["www.optoviki.kz"]
    start_urls = ["https://www.optovki.kz"]

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=10,
                dont_filter=True
            )

    def parse(self, response):
        # Сохраняем всю страницу для анализа
        with open('full_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Сохраняем все ссылки
        all_links = response.css('a::attr(href)').getall()
        with open('all_links.json', 'w', encoding='utf-8') as f:
            json.dump(all_links, f, ensure_ascii=False, indent=2)
        
        # Сохраняем все классы для анализа
        all_classes = []
        for element in response.css('*[class]'):
            classes = element.attrib.get('class', '').split()
            all_classes.extend(classes)
        
        unique_classes = list(set(all_classes))
        with open('all_classes.json', 'w', encoding='utf-8') as f:
            json.dump(unique_classes, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved full page, found {len(all_links)} links and {len(unique_classes)} unique classes")