from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLineEdit, QLabel, 
    QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange
)
from services.animal_service import get_animals, create_animal, update_animal, delete_animal

class AnimalWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zarządzanie Zwierzętami")

        # Przykładowe pola formularza
        self.name_input = QLineEdit()
        self.species_input = QLineEdit()
        self.owner_id_input = QLineEdit()

        self.create_button = QPushButton("Dodaj zwierzę")
        self.create_button.clicked.connect(self.handle_create_animal)

        # Tabela do wyświetlania listy zwierząt
        self.animals_table = QTableWidget()
        self.animals_table.setColumnCount(3)
        self.animals_table.setHorizontalHeaderLabels(["ID", "Nazwa", "Właściciel"])
        self.animals_table.cellClicked.connect(self.on_table_cell_clicked)

        # Przycisk do odświeżenia listy zwierząt
        self.refresh_button = QPushButton("Odśwież listę")
        self.refresh_button.clicked.connect(self.load_animals)

        # Przycisk do usuwania wybranego zwierzęcia
        self.delete_button = QPushButton("Usuń zaznaczone zwierzę")
        self.delete_button.clicked.connect(self.handle_delete_animal)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nazwa:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Gatunek:"))
        layout.addWidget(self.species_input)
        layout.addWidget(QLabel("Właściciel (ID):"))
        layout.addWidget(self.owner_id_input)
        layout.addWidget(self.create_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.animals_table)
        layout.addWidget(self.delete_button)

        self.load_animals()

    def load_animals(self):
        try:
            animals = get_animals()
            self.animals_table.setRowCount(len(animals))
            for row, animal in enumerate(animals):
                self.animals_table.setItem(row, 0, QTableWidgetItem(str(animal["id"])))
                self.animals_table.setItem(row, 1, QTableWidgetItem(animal["name"]))
                self.animals_table.setItem(row, 2, QTableWidgetItem(str(animal["owner_id"])))
        except Exception as e:
            print("Błąd podczas pobierania listy zwierząt:", e)

    def handle_create_animal(self):
        # Zbieramy dane z pól
        animal_data = {
            "name": self.name_input.text(),
            "species": self.species_input.text(),
            "owner_id": int(self.owner_id_input.text())
        }
        # Można dodać kolejne pola, np. breed, age itp.
        try:
            create_animal(animal_data)
            self.load_animals()
        except Exception as e:
            print("Błąd podczas tworzenia zwierzęcia:", e)

    def handle_delete_animal(self):
        current_row = self.animals_table.currentRow()
        if current_row < 0:
            print("Nie wybrano żadnego zwierzęcia.")
            return
        animal_id = self.animals_table.item(current_row, 0).text()
        try:
            delete_animal(animal_id)
            self.load_animals()
        except Exception as e:
            print("Błąd podczas usuwania zwierzęcia:", e)

    def on_table_cell_clicked(self, row, column):
        # Możemy tutaj obsłużyć kliknięcie w dany rekord,
        # np. wczytać dane do formularza, by je edytować
        pass
