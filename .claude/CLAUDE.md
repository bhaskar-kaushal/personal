# Claude Code Guidelines for Personal Project

This file provides guidance to Claude Code when working on the personal project and all sub-projects within it.

## Table of Contents
1. [Object-Oriented Programming Best Practices](#object-oriented-programming-best-practices)
2. [SOLID Principles](#solid-principles)
3. [Coding Standards](#coding-standards)
4. [Python Conventions](#python-conventions)
5. [Code Quality](#code-quality)
6. [Documentation](#documentation)
7. [Testing](#testing)
8. [Git Workflow](#git-workflow)

---

## Object-Oriented Programming Best Practices

### 1. **Encapsulation**

Hide internal details and expose only necessary interfaces.

```python
# ✅ GOOD - Encapsulation with private attributes
class BankAccount:
    def __init__(self, owner: str, balance: float):
        self._owner = owner
        self._balance = balance  # Private
    
    def deposit(self, amount: float) -> None:
        """Deposit money into account."""
        if amount > 0:
            self._balance += amount
    
    def get_balance(self) -> float:
        """Get current balance."""
        return self._balance

# ❌ AVOID - Exposing internals
class BankAccount:
    def __init__(self, owner: str, balance: float):
        self.owner = owner
        self.balance = balance  # Public, can be modified directly
```

### 2. **Inheritance**

Use inheritance to model "is-a" relationships.

```python
# ✅ GOOD - Proper inheritance hierarchy
class Animal:
    def __init__(self, name: str):
        self.name = name
    
    def make_sound(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def make_sound(self) -> str:
        return "Woof!"

class Cat(Animal):
    def make_sound(self) -> str:
        return "Meow!"

# ❌ AVOID - Deep inheritance chains
class A(Base): pass
class B(A): pass
class C(B): pass
class D(C): pass  # 5 levels deep
```

**Best Practices:**
- Keep inheritance depth ≤ 3 levels
- Prefer composition over inheritance
- Use abstract base classes for contracts

### 3. **Polymorphism**

Enable objects to be treated through a common interface.

```python
# ✅ GOOD - Polymorphic behavior
class PaymentProcessor:
    def process(self, payment_method) -> bool:
        return payment_method.pay()

class CreditCard:
    def pay(self) -> bool:
        print("Processing credit card...")
        return True

class PayPal:
    def pay(self) -> bool:
        print("Processing PayPal...")
        return True

processor = PaymentProcessor()
processor.process(CreditCard())  # Works
processor.process(PayPal())      # Also works
```

### 4. **Abstraction**

Define clear contracts through abstract classes and interfaces.

```python
from abc import ABC, abstractmethod

# ✅ GOOD - Abstract base class
class Database(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def query(self, sql: str) -> list:
        pass

class PostgreSQL(Database):
    def connect(self) -> None:
        print("Connecting to PostgreSQL...")
    
    def query(self, sql: str) -> list:
        return []  # Execute query
```

---

## SOLID Principles

### S - Single Responsibility Principle

**A class should have only one reason to change.**

```python
# ❌ AVOID - Multiple responsibilities
class User:
    def save_to_database(self) -> None:
        pass
    
    def send_email(self) -> None:
        pass
    
    def generate_report(self) -> None:
        pass

# ✅ GOOD - Single responsibility
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user: User) -> None:
        pass

class EmailService:
    def send(self, to: str, subject: str, body: str) -> None:
        pass

class ReportGenerator:
    def generate(self, user: User) -> str:
        pass
```

### O - Open/Closed Principle

**Classes should be open for extension, closed for modification.**

```python
# ❌ AVOID - Violates OCP
class ReportGenerator:
    def generate(self, report_type: str) -> str:
        if report_type == "pdf":
            return self._generate_pdf()
        elif report_type == "excel":
            return self._generate_excel()
        elif report_type == "csv":
            return self._generate_csv()
        # Adding new type requires modification

# ✅ GOOD - OCP compliant
from abc import ABC, abstractmethod

class Report(ABC):
    @abstractmethod
    def generate(self) -> str:
        pass

class PDFReport(Report):
    def generate(self) -> str:
        return "PDF content"

class ExcelReport(Report):
    def generate(self) -> str:
        return "Excel content"

class ReportGenerator:
    def __init__(self, report: Report):
        self.report = report
    
    def generate(self) -> str:
        return self.report.generate()
```

### L - Liskov Substitution Principle

**Derived classes must be substitutable for their base classes.**

```python
# ❌ AVOID - Violates LSP
class Bird:
    def fly(self) -> str:
        return "Flying"

class Penguin(Bird):
    def fly(self) -> str:
        raise NotImplementedError("Penguins can't fly")

# ✅ GOOD - LSP compliant
class Bird:
    def move(self) -> str:
        pass

class FlyingBird(Bird):
    def move(self) -> str:
        return "Flying"

class SwimmingBird(Bird):
    def move(self) -> str:
        return "Swimming"

class Penguin(SwimmingBird):
    def move(self) -> str:
        return "Swimming efficiently"
```

### I - Interface Segregation Principle

**Clients should not depend on interfaces they don't use.**

```python
# ❌ AVOID - Fat interface
class Worker(ABC):
    @abstractmethod
    def work(self) -> None:
        pass
    
    @abstractmethod
    def eat(self) -> None:
        pass

class Robot(Worker):
    def work(self) -> None:
        pass
    
    def eat(self) -> None:
        raise NotImplementedError("Robots don't eat")

# ✅ GOOD - Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self) -> None:
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self) -> None:
        pass

class Human(Workable, Eatable):
    def work(self) -> None:
        pass
    
    def eat(self) -> None:
        pass

class Robot(Workable):
    def work(self) -> None:
        pass
```

### D - Dependency Inversion Principle

**Depend on abstractions, not concrete implementations.**

```python
# ❌ AVOID - High-level depends on low-level
class EmailService:
    def send(self, to: str, subject: str) -> None:
        pass

class UserService:
    def __init__(self):
        self.email_service = EmailService()  # Tight coupling
    
    def register_user(self, email: str) -> None:
        # register logic
        self.email_service.send(email, "Welcome")

# ✅ GOOD - Dependency injection
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    def send(self, to: str, subject: str) -> None:
        pass

class EmailService(NotificationService):
    def send(self, to: str, subject: str) -> None:
        pass

class UserService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service  # Injected
    
    def register_user(self, email: str) -> None:
        # register logic
        self.notification_service.send(email, "Welcome")

# Usage
email_service = EmailService()
user_service = UserService(email_service)
```

---

## Coding Standards

### File Organization

```python
# 1. Module docstring
"""
Module description.

This module handles user authentication and session management.
"""

# 2. Imports (stdlib → third-party → local)
import os
import sys
from typing import List, Dict, Optional

from flask import Flask, request
from sqlalchemy import create_engine

from utils.logger import get_logger
from models.user import User

# 3. Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 4. Classes
class UserAuthentication:
    pass

# 5. Functions
def authenticate_user(username: str, password: str) -> bool:
    pass

# 6. Main block
if __name__ == "__main__":
    pass
```

### Naming Conventions

```python
# Functions and variables: snake_case
def calculate_total_price(items: list) -> float:
    pass

total_items = 10

# Classes: PascalCase
class UserService:
    pass

class DataProcessor:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30
API_KEY_LENGTH = 32

# Private members: _prefix
def _internal_helper(data: dict) -> None:
    pass

self._private_attribute = None

# Protected members: _prefix (convention, not enforced)
def _protected_method(self) -> None:
    pass
```

### Line Length and Formatting

```python
# ✅ GOOD - 100 character limit
def process_data(
    data: List[Dict[str, Any]], 
    filter_fn: Callable,
    sort_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Process and filter data."""
    filtered = [item for item in data if filter_fn(item)]
    if sort_key:
        filtered.sort(key=lambda x: x.get(sort_key))
    return filtered
```

### Type Hints

```python
# ✅ GOOD - Complete type hints
from typing import List, Dict, Optional, Union, Callable, Tuple

def fetch_user(user_id: int) -> Optional[Dict[str, str]]:
    pass

def process_records(
    records: List[Dict[str, Any]], 
    handler: Callable[[Dict], bool]
) -> Tuple[int, int]:
    success, failed = 0, 0
    for record in records:
        if handler(record):
            success += 1
        else:
            failed += 1
    return success, failed
```

---

## Python Conventions

### String Formatting

```python
# ✅ GOOD - F-strings (preferred)
name = "Alice"
message = f"Hello, {name}!"

# ✅ GOOD - .format() for complex cases
template = "User {}: {}"
formatted = template.format(user_id, user_name)

# ❌ AVOID - String concatenation
message = "Hello, " + name + "!"
```

### Exception Handling

```python
# ✅ GOOD - Specific exceptions
try:
    result = dangerous_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# ❌ AVOID - Catching everything
try:
    result = dangerous_operation()
except:
    pass
```

### Context Managers

```python
# ✅ GOOD - Use context managers
with open("file.txt", "r") as f:
    content = f.read()

# ✅ GOOD - Custom context manager
@contextmanager
def database_session():
    session = create_session()
    try:
        yield session
    finally:
        session.close()
```

### Comprehensions

```python
# ✅ GOOD - Readable comprehensions
squared = [x**2 for x in range(10)]
filtered = {k: v for k, v in data.items() if v > 0}
```

---

## Code Quality

### DRY - Don't Repeat Yourself

Avoid duplicating code. Abstract common patterns.

### KISS - Keep It Simple, Stupid

Write simple, clear code. Avoid over-engineering.

### YAGNI - You Aren't Gonna Need It

Don't add functionality that isn't currently needed.

---

## Documentation

### Docstrings

Use Google-style docstrings for all public functions:

```python
def calculate_discount(
    price: float, 
    discount_percent: float,
    min_price: float = 0.0
) -> float:
    """
    Calculate discounted price.
    
    Args:
        price: Original price.
        discount_percent: Discount percentage (0-100).
        min_price: Minimum allowed price.
    
    Returns:
        Discounted price, not less than min_price.
    
    Raises:
        ValueError: If discount_percent is outside 0-100 range.
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    
    discounted = price * (1 - discount_percent / 100)
    return max(discounted, min_price)
```

### Comments

Comments explain WHY, not WHAT:

```python
# ✅ GOOD - Explains reasoning
# Retry with exponential backoff for rate limit errors (API returns 429)
if attempt < max_attempts:
    time.sleep(2 ** attempt)
    return retry_request()

# ❌ AVOID - Obvious comments
# Increment counter
count += 1
```

---

## Testing

### Test Organization

```python
import unittest
from unittest.mock import Mock

class UserServiceTestCase(unittest.TestCase):
    """Tests for UserService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = Mock()
        self.service = UserService(self.repository)
    
    def test_get_user_returns_user_when_found(self):
        """Test that get_user returns user when found."""
        expected_user = User(id=1, name="Alice")
        self.repository.find.return_value = expected_user
        
        result = self.service.get_user(1)
        
        self.assertEqual(result, expected_user)
        self.repository.find.assert_called_once_with(1)
```

### Testing Best Practices

- Use AAA pattern: Arrange, Act, Assert
- One logical assertion per test (or related assertions)
- Use descriptive test names
- Mock external dependencies
- Write tests alongside code

---

## Git Workflow

### Commit Messages

**Format**: `type: description`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Build, CI/CD, dependencies

```bash
# ✅ GOOD
git commit -m "feat: Add user authentication

Implement JWT-based auth with token validation and refresh support."

# ❌ AVOID
git commit -m "fix stuff"
git commit -m "WIP"
```

### Branch Naming

```bash
# ✅ GOOD
feature/add-user-auth
bugfix/fix-null-pointer
refactor/improve-db-queries

# ❌ AVOID
feature/new
temp-branch
it
```

---

## Summary Checklist

### Before Writing Code
- [ ] Understand SOLID principles
- [ ] Review existing patterns
- [ ] Plan for testability
- [ ] Consider error handling

### During Development
- [ ] Follow naming conventions
- [ ] Add type hints (public functions)
- [ ] Write docstrings
- [ ] Keep functions small (SRP)
- [ ] Use DRY, KISS, YAGNI
- [ ] Write tests

### Before Committing
- [ ] Tests pass
- [ ] Code follows conventions
- [ ] No dead code
- [ ] Descriptive commit message

---

## Project Structure

### Primary Projects
- **rag-type**: RAG learning project with detailed conventions in `rag-type/.claude/conventions.md`
- Other sub-projects follow these guidelines

### Convention Priority
1. `<project>/.claude/conventions.md` — Project-specific (highest priority)
2. `<project>/.claude/CLAUDE.md` — Project guidance
3. `.claude/CLAUDE.md` (this file) — Personal project defaults

---

Last updated: 2026-09-25
