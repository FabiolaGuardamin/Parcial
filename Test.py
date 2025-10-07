from datetime import date, timedelta
import pytest

from src.library.repository import InMemoryRepo
from src.library.service import LibraryService, MAX_LOAN_DAYS
from src.library.models import Author
from src.library.exceptions import CopyNotAvailable, MaxLoansReached, ReaderBanned, NotFound

def setup_repo_with_book_and_copies(num_copies=3):
    repo = InMemoryRepo()
    service = LibraryService(repo)
    author = Author(name="Ian Sommerville", birthdate=date(1950,1,1))
    book, copies = service.add_book_and_copies("Software Engineering", 2020, author, edition="10th", num_copies=num_copies)
    return repo, service, book, copies

def test_borrow_and_return_on_time():
    repo, service, book, copies = setup_repo_with_book_and_copies(1)
    reader = service.register_reader("r1", "Alice")
    today = date(2025,1,1)
    copy = copies[0]
    borrowed = service.borrow_copy(reader.reader_id, copy.copy_id, today)
    assert borrowed.status == "borrowed"
    # return on time
    ret = service.return_copy(reader.reader_id, copy.copy_id, today + timedelta(days=10))
    assert ret["late_days"] == 0
    assert repo.get_reader("r1").banned_until is None

def test_max_loans_reached():
    repo, service, book, copies = setup_repo_with_book_and_copies(3)
    reader = service.register_reader("r2", "Bob")
    today = date(2025,1,1)
    # add three copies borrowed
    for i, copy in enumerate(copies):
        service.borrow_copy(reader.reader_id, copy.copy_id, today)
    with pytest.raises(MaxLoansReached):
        # create a new copy and try to borrow fourth
        _, copies2 = service.add_book_and_copies("Another", 2021, Author(name="X", birthdate=date(1970,1,1)), edition=None, num_copies=1)
        service.borrow_copy(reader.reader_id, copies2[0].copy_id, today)

def test_borrow_unavailable_copy_raises():
    repo, service, book, copies = setup_repo_with_book_and_copies(1)
    reader1 = service.register_reader("r3", "C1")
    reader2 = service.register_reader("r4", "C2")
    today = date(2025,1,1)
    copy = copies[0]
    service.borrow_copy(reader1.reader_id, copy.copy_id, today)
    with pytest.raises(CopyNotAvailable):
        service.borrow_copy(reader2.reader_id, copy.copy_id, today)
