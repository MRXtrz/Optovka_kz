# import scrapy
# from scrapy_selenium import SeleniumRequest
# from urllib.parse import urljoin
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# import logging
# import time

# from parser_service.src.services.parser_service import ParserService

# class OptovikiSpider(scrapy.Spider):
#     name = "optoviki"
#     allowed_domains = ["www.optoviki.kz"]
#     start_urls = ["https://www.optoviki.kz"]
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.parser_service = ParserService()
#     def start_requests(self):
#         for url in self.start_urls:
#             yield SeleniumRequest(
#                 url=url,
#                 callback=self.parse_categories,
#                 wait_time=15,
#                 wait_until=EC.presence_of_element_located((By.TAG_NAME, "body")),
#                 dont_filter=True
#             )
#     def parse_categories(self, response):
#         self.logger.info(f"Processing main page: {response.url}")
#         with open('debug_main_page.html', 'w', encoding='utf-8') as f:
#             f.write(response.text)
#         category_selectors = [
#             'ul.header-category a',
#             'nav a',
#             '.category a', 
#             '.menu a',
#             'a[href*="category"]',
#             'a[href*="catalog"]',
#             '.nav-link',
#             '.menu-item a'
#         ]
        
#         categories = None
#         used_selector = None
        
#         for selector in category_selectors:
#             categories = response.css(selector)
#             if categories:
#                 self.logger.info(f"Found {len(categories)} categories with selector: {selector}")
#                 used_selector = selector
#                 break
        
#         if not categories:
#             self.logger.warning("No categories found with any selector")
#             all_links = response.css('a::attr(href)').getall()
#             self.logger.info(f"All links found: {all_links[:10]}")
#             return

#         for cat in categories:
#             try:
#                 href = cat.css('::attr(href)').get()
#                 text = cat.css('::text').get()
#                 self.logger.info(f"Category: {text} -> {href}")
#                 if not href:
#                     continue
#                 url = urljoin(response.url, href)
#                 category_slug = self.parser_service.parse_category(cat, url)
#                 self.logger.info(f"Parsed category slug: {category_slug}")
                
#                 yield SeleniumRequest(
#                     url=url,
#                     callback=self.parse_suppliers,
#                     meta={'category_slug': category_slug},
#                     wait_time=10,
#                     dont_filter=True
#                 )
                
#             except Exception as e:
#                 self.logger.error(f"Error processing category {cat}: {e}")

#     def parse_suppliers(self, response):
#         category_slug = response.meta.get('category_slug')
#         self.logger.info(f"Parsing suppliers for category: {category_slug} at {response.url}")
        
#         # Сохраним HTML для отладки
#         with open(f'debug_suppliers_{category_slug}.html', 'w', encoding='utf-8') as f:
#             f.write(response.text)
        
#         # Пробуем разные селекторы для поставщиков
#         supplier_selectors = [
#             'div.supplier-card',
#             '.supplier',
#             '.company-card',
#             '.vendor-item',
#             '.seller-card',
#             'div.card',
#             '.list-item'
#         ]
        
#         suppliers = None
#         for selector in supplier_selectors:
#             suppliers = response.css(selector)
#             if suppliers:
#                 self.logger.info(f"Found {len(suppliers)} suppliers with selector: {selector}")
#                 break
        
#         if not suppliers:
#             self.logger.warning(f"No suppliers found for category {category_slug}")
#             return

#         for sup in suppliers[:2]: 
#             try:
#                 supplier_name = self.parser_service.parse_supplier(sup, category_slug)
#                 supplier_href = sup.css('a::attr(href)').get()
                
#                 if supplier_href:
#                     supplier_url = urljoin(response.url, supplier_href)
#                     self.logger.info(f"Following supplier: {supplier_name} -> {supplier_url}")
                    
#                     yield SeleniumRequest(
#                         url=supplier_url,
#                         callback=self.parse_products,
#                         meta={'supplier_name': supplier_name},
#                         wait_time=10,
#                         dont_filter=True
#                     )
                    
#             except Exception as e:
#                 self.logger.error(f"Error processing supplier: {e}")

#     def parse_products(self, response):
#         supplier_name = response.meta.get('supplier_name')
#         product_selectors = [
#             'div.product-item',
#             '.product-card',
#             '.item',
#             '.goods-item',
#             '.product',
#             'div.item'
#         ]
        
#         products = None
#         for selector in product_selectors:
#             products = response.css(selector)
#             if products:
#                 self.logger.info(f"Found {len(products)} products with selector: {selector}")
#                 break
        
#         if not products:
#             self.logger.warning(f"No products found for supplier {supplier_name}")
#             return

#         for prod in products[:3]:  # Ограничим для теста
#             try:
#                 self.parser_service.parse_product(prod, supplier_name)
#             except Exception as e:
#                 self.logger.error(f"Error processing product: {e}")

#         # Пагинация
#         next_page = response.css('a.next::attr(href), a.next-page::attr(href), .pagination a:contains("next")::attr(href)').get()
#         if next_page:
#             next_url = urljoin(response.url, next_page)
#             self.logger.info(f"Following next page: {next_url}")
#             yield SeleniumRequest(
#                 url=next_url,
#                 callback=self.parse_products,
#                 meta={'supplier_name': supplier_name},
#                 wait_time=10,
#                 dont_filter=True
#             )