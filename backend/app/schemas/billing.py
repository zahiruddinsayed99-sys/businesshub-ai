from pydantic import BaseModel, constr

class UpgradeRequest(BaseModel):
    cardNumber: constr(min_length=16, max_length=16, pattern=r'^[0-9]{16}$')
    expiryDate: constr(min_length=5, max_length=5, pattern=r'^(0[1-9]|1[0-2])\/?([0-9]{2})$')
    cvv: constr(min_length=3, max_length=4, pattern=r'^[0-9]{3,4}$')
    nameOnCard: str
