from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from ..db.db import SessionLocal, Category, Supplier, Product


class ParserDAO:
    @staticmethod
    def save_category(category: Category):
        with SessionLocal() as db:
            stmt = insert(Category).values(
                name=category.name,
                slug=category.slug
            ).on_conflict_do_nothing()

            db.execute(stmt)
            db.commit()

            result = db.execute(
                select(Category).where(Category.slug == category.slug)
            ).scalar_one_or_none()
            return result

    @staticmethod
    def save_supplier(supplier: Supplier):
        with SessionLocal() as db:
            existing = db.execute(
                select(Supplier).where(Supplier.name == supplier.name)
            ).scalar_one_or_none()

            if existing and existing.hash == supplier.hash:
                return existing

            stmt = insert(Supplier).values(
                name=supplier.name,
                description=supplier.description,
                image_url=supplier.image_url,
                category_id=supplier.category_id,
                contacts=supplier.contacts,
                hash=supplier.hash
            ).on_conflict_do_nothing()

            db.execute(stmt)
            db.commit()

            result = db.execute(
                select(Supplier).where(Supplier.name == supplier.name)
            ).scalar_one_or_none()
            return result

    @staticmethod
    def save_product(product: Product):
        with SessionLocal() as db:
            stmt = insert(Product).values(
                name=product.name,
                supplier_id=product.supplier_id,
                in_new=product.in_new,
                image_url=product.image_url
            ).on_conflict_do_nothing()

            db.execute(stmt)
            db.commit()

    @staticmethod
    def get_category_id(slug: str):
        with SessionLocal() as db:
            result = db.execute(
                select(Category.id).where(Category.slug == slug)
            ).scalar()
            return result

    @staticmethod
    def get_supplier_id(name: str):
        with SessionLocal() as db:
            result = db.execute(
                select(Supplier.id).where(Supplier.name == name)
            ).scalar()
            return result

    @staticmethod
    def get_category_by_slug(slug: str):
        with SessionLocal() as db:
            return db.execute(
                select(Category).where(Category.slug == slug)
            ).scalar_one_or_none()
