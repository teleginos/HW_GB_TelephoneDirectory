import sqlite3
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QLineEdit, QFileDialog
from PyQt5 import uic
import csv
import sys
import os


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ContactInforamationDialog(QDialog):
    def __init__(self, main_window, name, surname, phones, emails):
        super(ContactInforamationDialog, self).__init__()
        self.edit_contact_dialog = None
        uic.loadUi(resource_path('QtDesigner/ContactInformation.ui'), self)

        self.main_window = main_window
        self.name = name
        self.surname = surname
        self.phones = phones
        self.emails = emails

        self.label_name.setText(f"Имя: {name}")
        self.label_surname.setText(f"Фамилия: {surname}")
        self.label_phone.setText(f"Телефон: {', '.join(phones)}")
        self.label_email.setText(f"Email: {', '.join(emails)}")

        self.btn_delete.clicked.connect(self.delete_contact)
        self.btn_edit.clicked.connect(self.edit_contact)

    def delete_contact(self):
        self.main_window.delete_contact(self.name, self.surname)
        self.main_window.populate_list_widget()
        self.close()

    def edit_contact(self):
        try:
            self.edit_contact_dialog = AddContactDialog(self.main_window, edit=True,
                                                        existing_data=(self.name, self.surname,
                                                                       self.phones,
                                                                       self.emails))
            self.edit_contact_dialog.show()
            self.close()
        except Exception as e:
            print(f"Ошибка: {e}")


class AddContactDialog(QDialog):
    def __init__(self, main_window, edit=False, existing_data=None):
        super().__init__()
        uic.loadUi(resource_path('QtDesigner/AddContact.ui'), self)

        self.main_window = main_window
        self.edit = edit
        self.existing_data = existing_data

        if self.edit:
            self.label.setText("Изменение контакта")
            self.btn_add.setText("Сохранить")

        if self.edit and self.existing_data:
            self.lineEdit_firstName.setText(self.existing_data[0])
            self.lineEdit_lastName.setText(self.existing_data[1])
            self.lineEdit_phone.setText(self.existing_data[2][0])
            self.lineEdit_email.setText(self.existing_data[3][0])

        self.btn_add.clicked.connect(self.add_or_edit_contact)

    def add_or_edit_contact(self):
        first_name = self.lineEdit_firstName.text()
        last_name = self.lineEdit_lastName.text()
        phone = self.lineEdit_phone.text()
        email = self.lineEdit_email.text()

        if self.edit:
            self.main_window.update_contact(self.existing_data[0], self.existing_data[1], first_name, last_name,
                                            [phone], [email])
        else:
            self.main_window.add_contact(first_name, last_name, [phone], [email])

        self.main_window.populate_list_widget()
        self.close()


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.contact_information_dialog = None
        self.add_or_edit_contact = None
        self.cursor = None
        self.conn = None
        uic.loadUi(resource_path('QtDesigner/TelephoneDirectory.ui'), self)

        self.connect_to_database()
        self.populate_list_widget()

        self.btn_openAddContact.clicked.connect(self.open_add_contact_form)
        self.output_screen.itemClicked.connect(self.show_contacts_details)
        self.btn_import.clicked.connect(self.import_contacts)
        self.searchLineEdit.textChanged.connect(self.on_search)

    def on_search(self):
        search_text = self.searchLineEdit.text().lower()
        self.output_screen.clear()

        query = "SELECT last_name, first_name FROM contacts WHERE lower(first_name) LIKE ? OR lower(last_name) LIKE ?"
        self.cursor.execute(query, (f"{search_text}%", f"{search_text}%"))
        filtered_contacts = self.cursor.fetchall()

        for contact in filtered_contacts:
            last_name, first_name = contact
            self.output_screen.addItem(f"{last_name} {first_name}")

    def import_contacts(self):

        options = QFileDialog.Option()
        filePath, _ = QFileDialog.getOpenFileNames(self, "Выберите файл для импорта", "",
                                                   "CSV File (*.csv);;All Files (*)", options=options)
        if filePath:
            with open(filePath[0], 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                for row in csv_reader:
                    first_name, last_name, phone, email = row
                    self.add_contact(first_name, last_name, [phone], [email])
            self.populate_list_widget()

    def populate_list_widget(self):
        self.output_screen.clear()
        self.cursor.execute("SELECT last_name, first_name FROM contacts")
        all_contacts = self.cursor.fetchall()

        for contacts in all_contacts:
            last_name, first_name = contacts
            self.output_screen.addItem(f"{last_name} {first_name}")

    def open_add_contact_form(self):
        self.add_or_edit_contact = AddContactDialog(self)
        self.add_or_edit_contact.show()

    def connect_to_database(self):
        self.conn = sqlite3.connect('DataBase/phonebook.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS phones (
                id INTEGER PRIMARY KEY,
                contact_id INTEGER,
                phone TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                contact_id INTEGER,
                email TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')

        self.conn.commit()

    def add_contact(self, first_name, last_name, phones=None, emails=None):
        self.cursor.execute("INSERT INTO contacts (first_name, last_name) VALUES(?, ?)",
                            (first_name, last_name))
        contact_id = self.cursor.lastrowid

        if phones:
            for phone in phones:
                self.cursor.execute("INSERT INTO phones (contact_id, phone) VALUES(?, ?)",
                                    (contact_id, phone))

        if emails:
            for email in emails:
                self.cursor.execute("INSERT INTO emails (contact_id, email) VALUES(?, ?)",
                                    (contact_id, email))

        self.conn.commit()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

    def on_line_edit_clicked(self, event):
        self.search.setCursorPosition(0)
        QLineEdit.mousePressEvent(self.search, event)

    def show_contacts_details(self, item):
        try:
            surname, name = item.text().split(' ')
            self.cursor.execute("SELECT id FROM contacts WHERE first_name = ? AND last_name = ?", (name, surname))
            contact_id = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT phone FROM phones WHERE contact_id = ?", (contact_id,))
            phones = [phone[0] for phone in self.cursor.fetchall()]

            self.cursor.execute("SELECT email FROM emails WHERE contact_id = ?", (contact_id,))
            emails = [email[0] for email in self.cursor.fetchall()]

            self.contact_information_dialog = ContactInforamationDialog(self, name, surname, phones, emails)
            self.contact_information_dialog.show()
        except Exception as e:
            print(f'Ошибка: {e}')

    def delete_contact(self, name, surname):

        self.cursor.execute("SELECT id FROM contacts WHERE first_name = ? AND last_name = ?", (name, surname))
        contact_id = self.cursor.fetchone()[0]

        self.cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        self.cursor.execute("DELETE FROM phones WHERE contact_id = ?", (contact_id,))
        self.cursor.execute("DELETE FROM emails WHERE contact_id = ?", (contact_id,))

        self.conn.commit()
        self.populate_list_widget()

    def update_contact(self, old_first_name, old_last_name, new_first_name, new_last_name, phones, emails):

        self.cursor.execute("SELECT id FROM contacts WHERE first_name = ? AND last_name = ?", (old_first_name,
                                                                                               old_last_name))
        contact_id = self.cursor.fetchone()[0]

        self.cursor.execute("UPDATE contacts SET first_name = ?, last_name = ? WHERE id = ?", (new_first_name,
                                                                                               new_last_name,
                                                                                               contact_id))
        self.cursor.execute("UPDATE phones SET phone = ? WHERE contact_id = ?", (phones[0], contact_id))
        self.cursor.execute("UPDATE emails SET email = ? WHERE contact_id = ?", (emails[0], contact_id))

        self.conn.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
