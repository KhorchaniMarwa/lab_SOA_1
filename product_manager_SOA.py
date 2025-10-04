# product_manager_SOA.py

import logging
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Integer, Unicode, Float, ComplexModel, Fault
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from sqlalchemy import create_engine, Column, Integer as SQLInt, String, Float as SQLFloat
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------- Database Configuration -----------------
DB_USER = 'manager'
DB_PASSWORD = 'eniso123'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'myproducts'

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------- Database Setup -----------------
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(SQLInt, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    stock = Column(SQLInt, nullable=False)
    price = Column(SQLFloat, nullable=False)

Base.metadata.create_all(engine)

# ---------------- Spyne Complex Model for Product -----------------
class ProductInfo(ComplexModel):
    id = Integer
    name = Unicode
    stock = Integer
    price = Float

# ---------------- SOAP Service -------------------
class InventoryService(ServiceBase):

    @rpc(Unicode, Integer, Float, _returns=Integer)
    def CreateProduct(ctx, name, stock, price):
        if not name:
            raise Fault(faultcode="Client", faultstring="Name cannot be empty")
        if stock < 0 or price < 0:
            raise Fault(faultcode="Client", faultstring="Stock and price must be non-negative")
        session = Session()
        try:
            product = Product(name=name, stock=stock, price=price)
            session.add(product)
            session.commit()
            return product.id
        finally:
            session.close()

    @rpc(Integer, _returns=ProductInfo)
    def GetProduct(ctx, product_id):
        session = Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise Fault(faultcode="Client", faultstring=f"Product ID {product_id} not found")
            return ProductInfo(id=product.id, name=product.name, stock=product.stock, price=product.price)
        finally:
            session.close()

    @rpc(Integer, Unicode, Integer, Float, _returns=Unicode)
    def UpdateProduct(ctx, product_id, name, stock, price):
        session = Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise Fault(faultcode="Client", faultstring=f"Product ID {product_id} not found")
            if name:
                product.name = name
            if stock is not None:
                if stock < 0:
                    raise Fault(faultcode="Client", faultstring="Stock cannot be negative")
                product.stock = stock
            if price is not None:
                if price < 0:
                    raise Fault(faultcode="Client", faultstring="Price cannot be negative")
                product.price = price
            session.commit()
            return f"Product ID {product_id} updated successfully"
        finally:
            session.close()

    @rpc(Integer, _returns=Unicode)
    def DeleteProduct(ctx, product_id):
        session = Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise Fault(faultcode="Client", faultstring=f"Product ID {product_id} not found")
            session.delete(product)
            session.commit()
            return f"Product ID {product_id} deleted successfully"
        finally:
            session.close()

# ---------------- Spyne Application -------------------
application = Application(
    [InventoryService],
    tns='spyne.inventory.soap',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(application)

# ---------------- Run Server -------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("SOAP server running on http://localhost:8000")
    server = make_server('0.0.0.0', 8000, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped manually")
