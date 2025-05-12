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
    return {"access token":access_token,"token_type":"Bearer","id":user.id}


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


@app.put("/products/update/{product_id}")
def update_product(product_id: int, product: schemas.product, db: Session = Depends(get_session)):
    existing_product = db.query(models.Products).filter(models.Products.id == product_id).first()

    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_product.name = product.name
    existing_product.image = product.image
    existing_product.description = product.description
    existing_product.price = product.price
    existing_product.category = product.category
    existing_product.stock = product.stock

    db.commit()

    return {"message": "Product updated successfully"}


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


@app.post("/orders/create")
def create_order(
    order_data: schemas.CreateOrder,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    product = db.query(models.Products).filter(models.Products.id == order_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < order_data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    total_price = product.price * order_data.quantity
    print("..........",product)
    new_order = models.Orders(
        user_id=current_user.user_id,
        product_id=order_data.product_id,
        image = product.image,
        name = product.name,
        quantity=order_data.quantity,
        total_price=total_price,
        status="pending"
    )
    db.add(new_order)

    product.stock -= order_data.quantity

    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "product": product.name,
        "quantity": new_order.quantity,
        "total_price": new_order.total_price,
        "status": new_order.status
    }


@app.get("/orders")
def get_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_session)):
    orders = db.query(models.Orders).filter(models.Orders.user_id == current_user.id).all()

    if not orders:
        return {"message": "No orders found."}

    order_list = []
    for order in orders:
        product = db.query(models.Products).filter(models.Products.id == order.product_id).first()
        order_list.append({
            "order_id": order.id,
            "product_id": order.product_id,
            "image":product.image,
            "product_name": product.name if product else "Unknown",
            "quantity": order.quantity,
            "total_price": order.total_price,
            "created_at": order.created_at
        })

    return {"orders": order_list}


@app.delete("/cart/remove/{cart_item_id}")
def remove_from_cart(cart_item_id: int, current_user: models.User = Depends(get_current_user),
                     db: Session = Depends(get_session)):
    cart_item = db.query(models.Cart).filter(models.Cart.id == cart_item_id,
                                             models.Cart.user_id == current_user.id).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()

    return {"message": "Item removed from cart successfully"}




