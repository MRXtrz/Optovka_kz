import hashlib
import logging
from urllib.parse import urljoin
from datetime import datetime
from ..schemas.models import Category, Supplier, Product
from ..dao.dao import ParserDAO
from ..kafka.producer import KafkaNotifier
from ..exceptions.error import ScrapingError, DatabaseError
logger = logging.getLogger(__name__)
class ParserService:
    def __init__(self):
        self.dao = ParserDAO()
        self.notifier = KafkaNotifier()
    def _safe_text(self, response, selector: str, default: str = "") -> str:
        try:
            val = response.css(selector).get(default=default)
            return val.strip() if isinstance(val, str) else default
        except Exception:
            return default

    def _safe_attr(self, response, selector: str, default: str = "") -> str:
        try:
            val = response.css(selector).get(default=default)
            return val or default
        except Exception:
            return default

    def parse_category(self, response, url: str, name: str) -> str:
        try:
            slug = url.rstrip('/').split('/')[-1] if url else None
            if not slug:
                raise ScrapingError("Cannot determine category slug from URL")

            category = Category(name=name, slug=slug)

            try:
                saved = self.dao.save_category(category)
            except Exception as e:
                logger.exception("DB error while saving category")
                raise DatabaseError(f"DB error saving category {slug}: {e}")

            return slug

        except (DatabaseError, ScrapingError):
            raise
        except Exception as e:
            logger.exception("Unexpected error parsing category")
            raise ScrapingError(f"Failed to parse category: {e}")

    def parse_supplier(self, response, name, url, city, phone, category_slug):
        try:
            logger.info(f"Parsing supplier: {name} | City: {city} | Category: {category_slug}")

            category = self.dao.get_category_by_slug(category_slug)
            if not category:
                raise DatabaseError(f"Category with slug '{category_slug}' not found")

            unique_string = f"{name}-{url}-{city}-{phone}"
            supplier_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()

            contacts = {
                "city": city or "",
                "phone": phone or "",
                "url": url or ""
}


            supplier = Supplier(
                name=name,
                description=None,
                image_url=None,
                category_id=category.id,
                contacts=contacts,
                hash=supplier_hash
            )

            self.dao.save_supplier(supplier)
            logger.info(f"✅ Saved supplier: {name} ({city})")

        except Exception as e:
            logger.exception("Failed to parse supplier")
            raise ScrapingError(f"Failed to parse supplier {name}: {e}")

    def parse_product(self, response, supplier_name: str) -> None:
        try:
            name = self._safe_text(response, 'h3::text')
            if not name:
                name = self._safe_text(response, '.product-name::text') or "unknown-product"

            supplier_id = self.dao.get_supplier_id(supplier_name)
            if supplier_id is None:
                logger.warning("Supplier '%s' not found when parsing product '%s'", supplier_name, name)
            image_src = self._safe_attr(response, 'img::attr(src)', '')
            image_url = urljoin(response.url, image_src) if image_src else ""
            product = Product(
                name=name,
                supplier_id=supplier_id,
                in_new=True, 
                image_url=image_url
            )
            try:
                self.dao.save_product(product)
            except Exception as e:
                logger.exception("DB error while saving product")
                raise DatabaseError(f"DB error saving product {name}: {e}")
        except (DatabaseError, ScrapingError):
            raise
        except Exception as e:
            logger.exception("Unexpected error parsing product")
            raise ScrapingError(f"Failed to parse product: {e}")
