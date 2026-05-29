"""Seed roles, admin user, and neutral demo partners/products (no default supplier priority)."""

from app.core.database import SessionLocal
from app.core.permissions import ROLE_PERMISSION_PRESETS
from app.core.security import hash_password
from app.models import ManufacturingPartner, Product, ProductPartnerLink, Role, User


ROLE_NAMES = ["Admin", "Sales", "Supplier Manager", "Operations", "Viewer"]


def _role_permissions(name: str) -> dict[str, list[str]]:
    permissions = sorted(ROLE_PERMISSION_PRESETS.get(name.strip().lower(), set()))
    return {"permissions": permissions}


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(Role).count() == 0:
            for name in ROLE_NAMES:
                db.add(Role(name=name, permissions=_role_permissions(name)))
            db.commit()
        for role in db.query(Role).all():
            if not role.permissions:
                role.permissions = _role_permissions(role.name)
        db.commit()
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            raise RuntimeError("Admin role missing")
        if db.query(User).filter(User.email == "admin@example.com").first() is None:
            db.add(
                User(
                    email="admin@example.com",
                    full_name="Administrator",
                    password_hash=hash_password("admin123"),
                    role_id=admin_role.id,
                )
            )
            db.commit()

        if db.query(ManufacturingPartner).count() == 0:
            p1 = ManufacturingPartner(
                partner_name="Demo Lifting Systems Co.",
                partner_type="Lifting System Manufacturer",
                country="China",
                city="Shenzhen",
                notes="Demo partner for development. Equal weighting to others.",
            )
            p2 = ManufacturingPartner(
                partner_name="Demo Education Furniture Works",
                partner_type="Education Furniture Manufacturer",
                country="China",
                city="Chongqing",
                notes="Demo partner for development. Equal weighting to others.",
            )
            db.add_all([p1, p2])
            db.commit()
            db.refresh(p1)
            db.refresh(p2)

            prod1 = Product(
                product_name="Heavy-duty Adjustable Desk Frame (demo)",
                product_category="Adjustable Desk Frame",
                description="Demo catalog item for PartnerOS.",
            )
            prod2 = Product(
                product_name="Collaborative Learning Table (demo)",
                product_category="Education Furniture",
                description="Demo education furniture SKU.",
            )
            db.add_all([prod1, prod2])
            db.commit()
            db.refresh(prod1)
            db.refresh(prod2)

            db.add_all(
                [
                    ProductPartnerLink(product_id=prod1.id, manufacturing_partner_id=p1.id, is_preferred=False),
                    ProductPartnerLink(product_id=prod1.id, manufacturing_partner_id=p2.id, is_preferred=False),
                    ProductPartnerLink(product_id=prod2.id, manufacturing_partner_id=p2.id, is_preferred=False),
                ]
            )
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
