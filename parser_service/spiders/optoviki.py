import scrapy
from scrapy_selenium import SeleniumRequest
from urllib.parse import urljoin
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
from src.services.parser_service import ParserService


class OptovikiSpider(scrapy.Spider):
    name = "optoviki"
    allowed_domains = ["www.optoviki.kz"]
    start_urls = ["https://www.optoviki.kz"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_service = ParserService()

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_categories,
                wait_time=15,
                wait_until=EC.presence_of_element_located((By.TAG_NAME, "body")),
                dont_filter=True
            )
    def parse_categories(self, response):
        category_links = response.css('a[href*="optom-"]')

        if not category_links:
            self.logger.warning("No categories found on main page")
            with open('debug_main_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            return

        seen = set()

        for link in category_links:
            href = link.css('::attr(href)').get()
            name = link.css('::text').get()
            if not href or not name:
                continue
            if href in seen:
                continue
            seen.add(href)
            url = urljoin(response.url, href)
            name = name.strip()

            try:
                category_slug = self.parser_service.parse_category(response, url, name)
                print(f"{name} — {url}")
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении категории {name}: {e}")
                continue

            yield SeleniumRequest(
                url=url,
                callback=self.parse_suppliers,
                meta={'category_name': name, 'category_slug': category_slug},
                wait_time=10,
                dont_filter=True
            )

    def parse_suppliers(self, response):
            category_name = response.meta.get('category_name')
            category_slug = response.meta.get('category_slug')
            supplier_items = response.css('li.c-container')

            if not supplier_items:
                self.logger.warning(f"No suppliers found in category: {category_name}")
                with open(f'debug_suppliers_{category_slug}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return

            for item in supplier_items:
                name = None
                href = None
                city = None
                phone = None
                name = (item.css('.c-c-name a span::text').get()
                        or item.css('.c-c-name a::text').get()
                        or item.css('.c-c-name span::text').get())
                name = name.strip() if isinstance(name, str) else None

                href = item.css('.c-c-name a::attr(href)').get()
                if href:
                    href = urljoin(response.url, href)
                region_links = item.css('.c-c-region span a::text').getall()
                if region_links:
                    city = region_links[0].strip() if len(region_links) >= 1 else None
                else:
                    city = item.css("meta[itemprop='addressLocality']::attr(content)").get()
                phone = (item.css('.c-c-phone::text').get()
                        or item.css('.company-phone::text').get()
                        or None)
                phone = phone.strip() if isinstance(phone, str) else None
                self.logger.info(f"[SUPPLIER LIST] name={name!r} city={city!r} phone={phone!r} url={href!r} category={category_slug!r}")

                if href:
                    yield SeleniumRequest(
                        url=href,
                        callback=self.parse_supplier_detail,
                        meta={
                            'category_slug': category_slug,
                            'list_name': name,
                            'list_city': city,
                            'list_phone': phone,
                            'company_url': href
                        },
                        wait_time=8,
                        dont_filter=True
                    )
                else:
                    try:
                        self.parser_service.parse_supplier(
                            response=response,
                            name=name or "unknown",
                            url=None,
                            city=city,
                            phone=phone,
                            category_slug=category_slug
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to save supplier (no href) {name}: {e}")
                        continue

    def parse_supplier_detail(self, response):
        """Собираем подробности со страницы компании и сохраняем в БД через ParserService."""
        meta = response.meta or {}
        category_slug = meta.get('category_slug')
        list_name = meta.get('list_name')
        list_city = meta.get('list_city')
        list_phone = meta.get('list_phone')
        company_url = meta.get('company_url') or response.url

        name = (response.css('h1.firm-head-name::text').get()
                or response.css('.firm-head-name::text').get()
                or response.css('.c-c-name a span::text').get()
                or list_name)
        if isinstance(name, str):
            name = name.strip()
        city = (response.css('.firm-head-adress::text').get()
                or response.css('.firm-head-adress::text').get()
                or response.css("meta[itemprop='addressLocality']::attr(content)").get()
                or list_city)
        if isinstance(city, str):
            city = city.strip()

        phone = list_phone
        tel_href = response.xpath('//a[starts-with(@href, "tel:")]/@href').get()
        if tel_href:
            phone = tel_href.replace('tel:', '').strip()
        else:
            phone = (response.css('.firm-phones::text').get()
                     or response.css('.company-phone::text').get()
                     or response.css('.firm-contact .phone::text').get()
                     or phone)
        if isinstance(phone, str):
            phone = phone.strip()

        description = (response.css('.firm-about::text').get()
                       or response.css('.c-c-about::text').get()
                       or '').strip()
        image_src = response.css('.firm-logo img::attr(src), .c-c-logo img::attr(data-src), .c-c-logo img::attr(src)').get()
        image_url = urljoin(response.url, image_src) if image_src else None

        self.logger.info(f"[SUPPLIER DETAIL] name={name!r} city={city!r} phone={phone!r} url={company_url!r}")
        try:
            self.parser_service.parse_supplier(
                response=response,
                name=name or "unknown",
                url=company_url,
                city=city,
                phone=phone,
                category_slug=category_slug
            )
        except Exception as e:
            self.logger.exception(f"Failed to save supplier from detail page {company_url}: {e}")

