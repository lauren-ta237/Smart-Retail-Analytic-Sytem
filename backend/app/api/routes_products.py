# backend/app/api/routes_products.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/products")
def list_products():
    """
    Example endpoint: Returns a list of products.
    """
    return {
        "products": [
            {"id": 1, "name": "Product A", "price": 10.5},
            {"id": 2, "name": "Product B", "price": 25.0},
        ]
    }

@router.get("/products/{product_id}")
def get_product(product_id: int):
    """
    Example endpoint: Returns details of a single product by ID.
    """
    return {"id": product_id, "name": f"Product {product_id}", "price": 9.99}