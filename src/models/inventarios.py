from sqlalchemy import Column, Integer, Float, Boolean, UniqueConstraint
from src.database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    sede_id = Column(Integer, nullable=False)
    stock = Column(Float, default=0)
    activo = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("product_id", "sede_id", name="uq_product_sede"),
    )