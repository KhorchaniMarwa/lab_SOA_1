import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QMessageBox
)
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection
DB_USER = 'manager'
DB_PASSWORD = 'eniso123'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'myproducts'

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Product model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

Base.metadata.create_all(engine)

# GUI class
class ProductGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Manager")
        self.setGeometry(100, 100, 600, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Quantity", "Price"])
        self.layout.addWidget(self.table)

        # Input fields
        self.input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        self.input_layout.addWidget(self.name_input)
        self.input_layout.addWidget(self.quantity_input)
        self.input_layout.addWidget(self.price_input)
        self.layout.addLayout(self.input_layout)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Product")
        self.add_button.clicked.connect(self.add_product)
        self.update_button = QPushButton("Update Selected")
        self.update_button.clicked.connect(self.update_product)
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_product)
        self.refresh_button = QPushButton("Refresh Table")
        self.refresh_button.clicked.connect(self.load_products)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.update_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.refresh_button)
        self.layout.addLayout(self.button_layout)

        self.load_products()

    # Load products into table
    def load_products(self):
        products = session.query(Product).all()
        self.table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.table.setItem(row, 1, QTableWidgetItem(product.name))
            self.table.setItem(row, 2, QTableWidgetItem(str(product.quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{product.price:.2f}"))

    # Add product
    def add_product(self):
        name = self.name_input.text().strip()
        try:
            quantity = int(self.quantity_input.text())
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Quantity must be an integer and price must be a number.")
            return
        if quantity < 0 or price < 0 or not name:
            QMessageBox.warning(self, "Input Error", "Invalid input: no negative values or empty name allowed.")
            return
        product = Product(name=name, quantity=quantity, price=price)
        session.add(product)
        session.commit()
        QMessageBox.information(self, "Success", f"Product '{name}' added.")
        self.load_products()

    # Update selected product
    def update_product(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a product to update.")
            return
        product_id = int(self.table.item(selected, 0).text())
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            QMessageBox.warning(self, "Error", "Selected product not found.")
            return
        name = self.name_input.text().strip() or product.name
        try:
            quantity = int(self.quantity_input.text()) if self.quantity_input.text() else product.quantity
            price = float(self.price_input.text()) if self.price_input.text() else product.price
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Quantity must be an integer and price must be a number.")
            return
        if quantity < 0 or price < 0:
            QMessageBox.warning(self, "Input Error", "Negative values are not allowed.")
            return
        product.name = name
        product.quantity = quantity
        product.price = price
        session.commit()
        QMessageBox.information(self, "Success", f"Product ID {product_id} updated.")
        self.load_products()

    # Delete selected product
    def delete_product(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a product to delete.")
            return
        product_id = int(self.table.item(selected, 0).text())
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            QMessageBox.warning(self, "Error", "Selected product not found.")
            return
        session.delete(product)
        session.commit()
        QMessageBox.information(self, "Success", f"Product ID {product_id} deleted.")
        self.load_products()

# Run application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ProductGUI()
    gui.show()
    sys.exit(app.exec_())
