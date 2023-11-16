import time
import datetime
import json


class User:
    MIN_BALANCE = 5000

    def __init__(self, user_id, password):
        self.user_id = user_id
        self.password = password
        self.balance = self.MIN_BALANCE
        self.login_attempts = 0
        self.is_locked = False
        self.transaction_history = []

    def deposit(self, amount, denominations):
        denominations = {int(denomination): int(count) for denomination, count in denominations.items()}
        total_deposit = sum([denomination * count for denomination, count in denominations.items()])
        if total_deposit <= 100000:
            self.balance += total_deposit
            self._update_transaction_history(f"Deposited ${total_deposit} on {self._current_time()}")
            return True
        else:
            print("Exceeded maximum deposit limit.")
            return False

    def withdraw(self, amount, denominations):
        denominations = {int(denomination): int(count) for denomination, count in denominations.items()}
        total_withdrawal = sum([denomination * count for denomination, count in denominations.items()])
        if total_withdrawal <= 50000 and self.balance - total_withdrawal >= self.MIN_BALANCE:
            self.balance -= total_withdrawal
            self._update_transaction_history(f"Withdrew ${total_withdrawal} on {self._current_time()}")
            return True
        else:
            print("Invalid withdrawal amount or insufficient funds.")
            return False

    def check_balance(self):
        return self.balance

    def change_credentials(self, current_password, new_password):
        if self.password == current_password:
            self.password = new_password
            return True
        else:
            print("Invalid current password. Unable to change credentials.")
            return False

    def add_tag_to_last_transaction(self, tag):
        if self.transaction_history:
            last_transaction = self.transaction_history[-1]
            last_transaction_with_tag = f"{last_transaction} [Tag: {tag}]"
            self.transaction_history[-1] = last_transaction_with_tag
        else:
            print("No transactions available to add a tag.")

    def _current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")

    def _update_transaction_history(self, transaction):
        self.transaction_history.append(transaction)


class Admin(User):
    MAX_BALANCE = 300000
    MAX_DEPOSIT = 300000

    def __init__(self, user_id, password):
        super().__init__(user_id, password)

    def total_balance(self, user_balances):
        total_balance = sum(user_balances.values())
        return total_balance

    def total_deposit(self, deposits):
        total_deposit = sum([sum([denomination * count for denomination, count in deposit.items()]) for deposit in deposits])
        return total_deposit

    def cash_deposit(self, amount, denominations):
        total_deposit = sum([denomination * count for denomination, count in denominations.items()])
        if total_deposit <= self.MAX_DEPOSIT:
            self.balance += total_deposit
            self._update_transaction_history(f"Admin deposited ${total_deposit} on {self._current_time()}")
            return True
        else:
            print("Exceeded maximum deposit limit for admin.")
            return False

    def notify_low_balance(self):
        if self.balance < 75000:
            print("Notification: Admin balance is less than 75k.")


class ATM:
    TIMEOUT_LIMIT = 30

    def __init__(self):
        self.users = {}
        self.admin = Admin("admin", "admin_pass")
        self.load_data()

    def load_data(self):
        try:
            with open("users.json", "r") as file:
                data = json.load(file)
                for user_id, user_data in data.items():
                    if user_id == "admin":
                        self.admin.balance = user_data["balance"]
                        self.admin.transaction_history = user_data["transaction_history"]
                    else:
                        user = User(user_id, user_data["password"])
                        user.balance = user_data["balance"]
                        user.login_attempts = user_data["login_attempts"]
                        user.is_locked = user_data["is_locked"]
                        user.transaction_history = user_data["transaction_history"]
                        self.users[user_id] = user
        except FileNotFoundError:
            pass

    def save_data(self):
        data = {"admin": {
                    "password": self.admin.password,
                    "balance": self.admin.balance,
                    "transaction_history": self.admin.transaction_history
                }}
        for user_id, user in self.users.items():
            data[user_id] = {
                "password": user.password,
                "balance": user.balance,
                "login_attempts": user.login_attempts,
                "is_locked": user.is_locked,
                "transaction_history": user.transaction_history
            }
        with open("users.json", "w") as file:
            json.dump(data, file)

    def create_account(self, user_id, password):
        if user_id not in self.users:
            self.users[user_id] = User(user_id, password)
            self.save_data()
            print("Account created successfully!")
        else:
            print("User ID already exists. Please choose a different one.")

    def change_credentials(self, user_id, current_password, new_password):
        user = self.users.get(user_id)
        if user:
            if user.change_credentials(current_password, new_password):
                self.save_data()
                print(f"Credentials changed successfully for user {user_id}!")
        else:
            print("User not found. Unable to change credentials.")

    def check_timeout(self, last_interaction_time):
        elapsed_time = time.time() - last_interaction_time
        if elapsed_time >= self.TIMEOUT_LIMIT:
            print("\n<<Time limit exceeded. Logout due to inactivity.>>")
            return True
        return False

    def login(self, user_id, password):
        user = self.users.get(user_id)
        if user and not user.is_locked:
            if user.password == password:
                user.login_attempts = 0
                return user
            else:
                user.login_attempts += 1
                if user.login_attempts >= 3:
                    user.is_locked = True
                    print("Account locked due to multiple login failures.")
                else:
                    print("Invalid Password. Attempts remaining:", 3 - user.login_attempts)
        elif user and user.is_locked:
            print("Account is locked. Please contact customer support.")
        else:
            print("\n<<Invalid User ID. Please try again.>>")
        return None

    def display_transaction_history(self, user):
        print("\nTransaction History:")
        for transaction in user.transaction_history:
            print(transaction)

    def admin_menu(self):
        last_interaction_time = time.time()

        while True:
            print("\n------Admin Menu------")
            print("\n(1) Total Balance\n(2) Total Deposit\n(3) Admin Deposit\n(4) Notify Low Balance\n(5) Logout")
            admin_choice = input("\n=> Enter your choice: ")

            if admin_choice == "1":
                total_balance = self.admin.total_balance({user_id: user.balance for user_id, user in self.users.items()})
                print("Total Balance: $", total_balance)
            elif admin_choice == "2":
                total_deposit = self.admin.total_deposit(
                    [{denomination: count for denomination, count in json.loads(user_data["transaction_history"])[-1]["denominations"].items()} for user_id, user_data in self.users.items()]
                )
                print("Total Deposit: $", total_deposit)
            elif admin_choice == "3":
                amount = int(input("Enter deposit amount for admin: $"))
                denominations = self._get_denominations()
                if self.admin.cash_deposit(amount, denominations):
                    print("Admin Deposit successful!")
            elif admin_choice == "4":
                self.admin.notify_low_balance()
            elif admin_choice == "5":
                print("\n<<Admin Logout successful!>>")
                break
            else:
                print("\n<<Invalid choice. Please try again.>>")

            if self.check_timeout(last_interaction_time):
                break

    def user_menu(self, user):
        last_interaction_time = time.time()

        while True:
            print("\n(1) Check Balance\n(2) Deposit\n(3) Withdraw\n(4) Change Password\n(5) Transaction History\n(6) Add Tag to Last Transaction\n(7) Logout")
            user_choice = input("\n=> Enter your choice: ")

            if user_choice:
                last_interaction_time = time.time()

                if user_choice == "1":
                    print("Your balance: $", user.check_balance())
                elif user_choice == "2":
                    amount = int(input("Enter deposit amount: $"))
                    denominations = self._get_denominations()
                    if user.deposit(amount, denominations):
                        print("Deposit successful!")
                elif user_choice == "3":
                    amount = int(input("Enter withdrawal amount: $"))
                    denominations = self._get_denominations()
                    if user.withdraw(amount, denominations):
                        print("Withdrawal successful!")
                    else:
                        print("\n<<Transaction failed!>>")
                elif user_choice == "4":
                    current_password = input("Enter current password: ")
                    new_password = input("Enter new password: ")
                    self.change_credentials(user.user_id, current_password, new_password)
                elif user_choice == "5":
                    self.display_transaction_history(user)
                elif user_choice == "6":
                    tag = input("Enter tag for the last transaction: ")
                    user.add_tag_to_last_transaction(tag)
                    print("Tag added to the last transaction.")
                elif user_choice == "7":
                    print("\n<<Logout successful!>>")
                    break
                else:
                    print("\n<<Invalid choice. Please try again.>>")

                if self.check_timeout(last_interaction_time):
                    break

    def main(self):
        while True:
            print("\t\t", "-" * 80)
            print("\t\t|", "\t\t\t*** Hello, Welcome to the Enhanced ATM ***", "\t\t\t |")
            print("\t\t", "-" * 80)
            print("\n------Bank Menu------")
            print("\n(1) Create Account\n(2) Login\n(3) Admin Login\n(4) Exit")
            choice = input("\n=> Enter your choice: ")

            last_interaction_time = time.time()

            if choice == "1":
                user_id = input("\nEnter User ID: ")
                password = input("Enter Password: ")
                self.create_account(user_id, password)
            elif choice == "2":
                user_id = input("Enter User ID: ")
                password = input("Enter Password: ")
                user = self.login(user_id, password)

                if user:
                    print("Login successful!")
                    while True:
                        self.user_menu(user)
                        if self.check_timeout(last_interaction_time):
                            break
            elif choice == "3":
                admin_id = input("Enter Admin ID: ")
                admin_password = input("Enter Admin Password: ")
                admin = self.login(admin_id, admin_password)
                if admin:
                    print("Admin Login successful!")
                    while True:
                        self.admin_menu()
                        if self.check_timeout(last_interaction_time):
                            break
            elif choice == "4":
                print("\nThank you for using the ATM. Goodbye!")
                self.save_data()
                break
            else:
                print("\n<<Invalid choice. Please try again.>>")

            if self.check_timeout(last_interaction_time):
                break

            # Check for timeout every iteration
            if self.check_timeout(last_interaction_time):
                break

    def _get_denominations(self):
        denominations_str = input('Enter denominations (e.g., {"100": 2, "200": 5}): ')
        return json.loads(denominations_str)


if __name__ == "__main__":
    atm = ATM()
    atm.main()

