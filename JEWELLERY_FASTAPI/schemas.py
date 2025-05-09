from pydantic import BaseModel,EmailStr

class registerUser(BaseModel):
    username: str
    email: EmailStr
    password: str

class loginUser(BaseModel):
    email: EmailStr
    password: str

class category(BaseModel):
    name: str

class product(BaseModel):
    name:  str
    image: str
    description: str
    price :  float
    category: str
    stock: int

class cartItem(BaseModel):
    user_id: int
    product_id: int
    quantity: int

# class showCartItems(BaseModel):
#     user_id: int


