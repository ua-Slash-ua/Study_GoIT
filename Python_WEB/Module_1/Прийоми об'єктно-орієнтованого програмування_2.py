import pickle
from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime, timedelta


# Абстрактний клас інтерфейсу
class UserInterface(ABC):
    @abstractmethod
    def show_contact(self, record):
        pass

    @abstractmethod
    def show_all_contacts(self, book):
        pass

    @abstractmethod
    def show_commands(self):
        pass

# Реалізація консольного інтерфейсу
class ConsoleInterface(UserInterface):
    def show_contact(self, record):
        phones = ', '.join(phone.value for phone in record.phones)
        birthday = record.birthday.value.strftime("%d.%m.%Y") if record.birthday else "N/A"
        print(f"Contact name: {record.name.value}, phones: {phones}, birthday: {birthday}")

    def show_all_contacts(self, book):
        for record in book.values():
            self.show_contact(record)

    def show_commands(self):
        print("Available commands:")
        print("add <name> <phone> - Add a new contact")
        print("change <name> <old phone> <new phone> - Change phone")
        print("phone <name> - Show contact phones")
        print("add-birthday <name> <birthday> - Add birthday to contact")
        print("show-birthday <name> - Show contact's birthday")
        print("birthdays - Show upcoming birthdays")
        print("all - Show all contacts")
        print("close/exit - Exit the program")


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        self.value = self.audit_number(value)

    def audit_number(self, input_number):
        if len(input_number) == 10 and input_number.isdigit():
            return input_number
        else:
            raise ValueError('Неправильно введений номер телефону')


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        try:
            phone = Phone(phone_number)
            self.phones.append(phone)
        except ValueError as e:
            return str(e)

    def remove_phone(self, phone_number):
        try:
            formatted_number = Phone(phone_number).value
        except ValueError as e:
            return str(e)

        for phone in self.phones:
            if phone.value == formatted_number:
                self.phones.remove(phone)
                return "Phone removed."
        return "Phone not found."

    def edit_phone(self, old_number, new_number):
        try:
            formatted_old_number = Phone(old_number).value
            new_phone = Phone(new_number)
        except ValueError as e:
            return str(e)

        for i, phone in enumerate(self.phones):
            if phone.value == formatted_old_number:
                self.phones[i] = new_phone
                return "Phone updated."
        return "Old phone number not found."

    def find_phone(self, number_phone):
        try:
            formatted_number = Phone(number_phone).value
        except ValueError as e:
            return str(e)

        for phone in self.phones:
            if phone.value == formatted_number:
                return phone
        return None

    def add_birthday(self, value):
        try:
            self.birthday = Birthday(value)
        except ValueError as e:
            return str(e)

    def __str__(self):
        phones = ', '.join(phone.value for phone in self.phones)
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "N/A"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                next_birthday = record.birthday.value.replace(year=today.year)
                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)
                if 0 <= (next_birthday - today).days <= 7:
                    if next_birthday.weekday() > 4:
                        next_birthday += timedelta(days=(7 - next_birthday.weekday()))
                    upcoming_birthdays.append({"name": record.name.value, "birthday": next_birthday.strftime("%d.%m.%Y")})
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(f"{name}: {record}" for name, record in self.data.items())


def input_error(handler):
    def wrapper(*args):
        try:
            return handler(*args)
        except (KeyError, ValueError, IndexError) as e:
            return str(e)
    return wrapper


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    result = record.add_birthday(birthday)
    if result:
        return result
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    if record.birthday:
        return f"{name}'s birthday is {record.birthday.value.strftime('%d.%m.%Y')}."
    else:
        return f"No birthday found for {name}."


@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No birthdays in the next 7 days."
    return "\n".join(f"{entry['name']}: {entry['birthday']}" for entry in upcoming_birthdays)


@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        result = record.edit_phone(old_phone, new_phone)
        return result if result else "Phone updated."
    return "Contact not found."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(phone.value for phone in record.phones)}"
    return "Contact not found."


def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower()
    args = parts[1:]
    return command, args


# Інтегруємо інтерфейс в основну програму
def main():
    book = load_data()
    ui = ConsoleInterface()  # Використовуємо консольний інтерфейс

    print("Welcome to the assistant bot!")
    ui.show_commands()

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            record = book.find(args[0])
            if record:
                ui.show_contact(record)
            else:
                print("Contact not found.")

        elif command == "all":
            ui.show_all_contacts(book)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()