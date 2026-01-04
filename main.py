import sys
import sqlite3
import os
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from main_ui import Ui_MainWindow
from addEditCoffeeForm import Ui_Dialog


class DatabaseManager:
    def __init__(self, db_path='data/coffee.sql'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coffee (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    [название сорта] TEXT NOT NULL,
                    [степень обжарки] TEXT NOT NULL,
                    [тип ] TEXT NOT NULL,
                    [описание вкуса] TEXT,
                    [цена ] REAL NOT NULL,
                    [объём упаковки] REAL NOT NULL
                )
            """)
            connection.commit()
            connection.close()
        except sqlite3.Error as e:
            raise Exception(f"Ошибка инициализации базы данных: {e}")

    def get_all_coffee(self):
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM coffee")
            records = cursor.fetchall()
            connection.close()
            return records
        except sqlite3.Error as e:
            raise Exception(f"Ошибка получения данных: {e}")

    def get_coffee_by_id(self, coffee_id):
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM coffee WHERE id = ?", (coffee_id,))
            record = cursor.fetchone()
            connection.close()
            return record
        except sqlite3.Error as e:
            raise Exception(f"Ошибка получения данных: {e}")

    def save_coffee(self, name, roast, coffee_type, description, price, volume, coffee_id=None):
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            if coffee_id:
                cursor.execute("""
                    UPDATE coffee
                    SET [название сорта] = ?, [степень обжарки] = ?, [тип ] = ?,
                        [описание вкуса] = ?, [цена ] = ?, [объём упаковки] = ?
                    WHERE id = ?
                """, (name, roast, coffee_type, description, price, volume, coffee_id))
            else:
                cursor.execute("""
                    INSERT INTO coffee ([название сорта], [степень обжарки], [тип ], [описание вкуса], [цена ],
[объём упаковки])
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, roast, coffee_type, description, price, volume))

            connection.commit()
            connection.close()
        except sqlite3.Error as e:
            raise Exception(f"Ошибка сохранения данных: {e}")


class AddEditCoffeeForm(QtWidgets.QDialog):
    def __init__(self, db_manager, coffee_id=None):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.db_manager = db_manager
        self.coffee_id = coffee_id

        self.setup_ui()

        if coffee_id:
            self.load_coffee_data()

    def setup_ui(self):
        self.ui.buttonBox.accepted.connect(self.save_coffee)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.priceSpinBox.setMinimum(0)
        self.ui.priceSpinBox.setMaximum(999999)
        self.ui.volumeSpinBox.setMinimum(0)
        self.ui.volumeSpinBox.setMaximum(999999)

    def load_coffee_data(self):
        try:
            record = self.db_manager.get_coffee_by_id(self.coffee_id)
            if record:
                self.ui.nameLineEdit.setText(record[1])
                self.ui.roastLineEdit.setText(record[2])
                self.ui.typeLineEdit.setText(record[3])
                self.ui.descriptionTextEdit.setPlainText(record[4] or "")
                self.ui.priceSpinBox.setValue(record[5])
                self.ui.volumeSpinBox.setValue(record[6])
            else:
                QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.reject()

    def validate_input(self):
        if not self.ui.nameLineEdit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название сорта")
            return False
        if not self.ui.roastLineEdit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите степень обжарки")
            return False
        if not self.ui.typeLineEdit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите тип кофе")
            return False
        if self.ui.priceSpinBox.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Цена должна быть больше 0")
            return False
        if self.ui.volumeSpinBox.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Объем должен быть больше 0")
            return False
        return True

    def save_coffee(self):
        if not self.validate_input():
            return

        try:
            name = self.ui.nameLineEdit.text().strip()
            roast = self.ui.roastLineEdit.text().strip()
            coffee_type = self.ui.typeLineEdit.text().strip()
            description = self.ui.descriptionTextEdit.toPlainText().strip()
            price = self.ui.priceSpinBox.value()
            volume = self.ui.volumeSpinBox.value()

            self.db_manager.save_coffee(name, roast, coffee_type, description, price, volume, self.coffee_id)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class CoffeeApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db_manager = DatabaseManager()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.ui.addButton.clicked.connect(self.add_coffee)
        self.ui.editButton.clicked.connect(self.edit_coffee)

        self.ui.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def load_data(self):
        try:
            records = self.db_manager.get_all_coffee()
            self.ui.tableWidget.setRowCount(len(records))
            self.ui.tableWidget.setColumnCount(7)
            self.ui.tableWidget.setHorizontalHeaderLabels([
                "ID", "Название сорта", "Степень обжарки",
                "Молотый/в зернах", "Описание вкуса", "Цена", "Объем упаковки"
            ])

            self.ui.tableWidget.setColumnWidth(0, 50)   
            self.ui.tableWidget.setColumnWidth(1, 150) 
            self.ui.tableWidget.setColumnWidth(2, 120) 
            self.ui.tableWidget.setColumnWidth(3, 120)  
            self.ui.tableWidget.setColumnWidth(4, 200)  
            self.ui.tableWidget.setColumnWidth(5, 80)   
            self.ui.tableWidget.setColumnWidth(6, 100)  

            for i, row in enumerate(records):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  
                    self.ui.tableWidget.setItem(i, j, item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def add_coffee(self):
        try:
            dialog = AddEditCoffeeForm(self.db_manager)
            if dialog.exec():
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def edit_coffee(self):
        selected_items = self.ui.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        try:
            row = selected_items[0].row()
            coffee_id_item = self.ui.tableWidget.item(row, 0)
            if coffee_id_item:
                coffee_id = int(coffee_id_item.text())
                dialog = AddEditCoffeeForm(self.db_manager, coffee_id)
                if dialog.exec():
                    self.load_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Некорректная запись")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректный ID записи")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


def main():
    try:
        app = QtWidgets.QApplication(sys.argv)
        window = CoffeeApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
