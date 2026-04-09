from pydantic import BaseModel, validator
from typing import Optional

# Schemas de inventario
class InventoryCreate(BaseModel):
    product_id: int
    sede_id: int
    stock: float

    @validator("stock")
    def stock_not_negative(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v
#  Actualización de inventario
class InventoryUpdate(BaseModel):
    stock: float

    @validator("stock")
    def stock_not_negative(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v
# Respuesta de inventario
class InventoryResponse(BaseModel):
    id: int
    product_id: int
    sede_id: int
    stock: float
    activo: bool

    class Config:
        orm_mode = True