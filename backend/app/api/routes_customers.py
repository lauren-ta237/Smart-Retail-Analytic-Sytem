from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.schemas.customer_schema import CustomerCreate, Customer
from backend.app.services.customer_service import create_customer, update_exit_time
from backend.app.core.database import get_db

# Fix: instantiate APIRouter
router = APIRouter()

# POST endpoint to add a new customer
@router.post("/", response_model=Customer)
def add_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, customer)

# PUT endpoint to mark customer exit
@router.put("/{customer_id}/exit", response_model=Customer)
def customer_exit(customer_id: int, db: Session = Depends(get_db)):
    return update_exit_time(db, customer_id)