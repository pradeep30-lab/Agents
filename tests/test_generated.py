import pytest
from playwright.sync_api import Page
from pages.generated_page import TodoPage


@pytest.fixture(scope="function")
def todo_page(page: Page) -> TodoPage:
    return TodoPage(page)


def test_add_and_verify_todo_item(todo_page: TodoPage):
    todo_page.navigate()
    todo_page.add_todo_item("Buy Milk")
    assert todo_page.is_todo_item_visible("Buy Milk")
