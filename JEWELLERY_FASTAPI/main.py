from fastapi import FastAPI, Depends,HTTPException, Request, status
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import JSONResponse

from JEWELLERY_FASTAPI import models, schemas, auth_service
from JEWELLERY_FASTAPI.database import (engine, SessionLocal)
from sqlalchemy.orm import Session
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app = FastAPI()


origins = ["*"]

origins = [
    "http://127.0.0.1:8000",
    "*",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    session=SessionLocal()
    try:
        yield session
    finally:
        session.close()


from jose import jwt, JWTError

def get_current_user(request: Request, db: Session=Depends(get_session)):
    credentials_exception =HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    auth_header = request.headers.get("Authorization")
    if auth_header is None or not auth_header.startswith("Bearer "):
        raise credentials_exception
    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user is None:
        raise credentials_exception
    return user



@app.get("/hello")
def say_hello():
    return {"message": "Hello, World!"}

@app.post("/register")
def register_user(user:schemas.registerUser,db:Session = Depends(get_session)):
    existing_user = db.query(models.User).filter_by(email = user.email).first()
    if existing_user:
        raise HTTPException(status_code=400,detail="email already registered")
    hashed_password=password_context.hash(user.password)
    new_user =  models.User(username=user.username,email=user.email,password=hashed_password)

    db.add(new_user)
    db.commit()
    return {"message":"user created successfully"}

@app.post("/login")
def login(form_data: schemas.loginUser, db: Session=Depends(get_session)):
    user=db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not auth_service.verify_password(form_data.password,user.password):
        raise HTTPException(status_code=400,detail="Incorrect email or password")
    access_token = auth_service.create_access_token(data={"sub":str(user.id)})
    return {"access token":access_token,"token_type":"Bearer"}


@app.get("/verify-token", response_model=schemas.loginUser)
def verify_token(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/products/add")
def add_product(product:schemas.product, db: Session = Depends(get_session)):
    new_product = models.Products(name = product.name,image = product.image,description = product.description,price = product.price,category=product.category, stock = product.stock)
    db.add(new_product)
    db.commit()
    return {"message":"Product added successfully"}


@app.get("/products")
def get_products(db: Session = Depends(get_session)):
    products = db.query(models.Products).all()
    if not products:
        return {"message": "No products found."}

    product_list = []
    for product in products:
        product_list.append({
            "id": product.id,
            "name": product.name,
            "image": product.image,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category": product.category
        })

    return {"products": product_list}


@app.get("/cart/items")
def get_cart_items(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_session)):
    cart_items = (
        db.query(models.Cart)
        .filter(models.Cart.user_id==current_user.id)
        .all()
    )
    if not cart_items:
        return {"message": "Your cart is empty."}

    items = []
    for item in cart_items:
        product = db.query(models.Products).filter(models.Products.id == item.product_id).first()
        if product:
            items.append({
                "cart_item_id": item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_image": product.image,
                "quantity": item.quantity,
                "price_per_item": product.price,
                "total_price": product.price * item.quantity
            })

    return {"cart_items": items}



@app.post("/cart/add")
def add_to_cart(cart_item:schemas.cartItem, current_user:models.User = Depends(get_current_user),db: Session = Depends(get_session)):
    if not current_user or current_user.id!=cart_item.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid user or token")
    product =  db.query(models.Products).filter(models.Products.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    existing_cart_item = db.query(models.Cart).filter_by(user_id = current_user.id,product_id=cart_item.product_id).first()
    if existing_cart_item:
        existing_cart_item.quantity +=cart_item.quantity
    else:
        new_cart_item = models.Cart(user_id = current_user.id,product_id = cart_item.product_id, quantity = cart_item.quantity)
        db.add(new_cart_item)
    db.commit()
    return {"message":"item added to cart successfully"}

