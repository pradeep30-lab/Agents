from playwright.sync_api import Page


class TodoPage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self):
        self.page.goto("https://demo.playwright.dev/todomvc")

    def add_todo_item(self, item_text: str):
        self.page.locator("input.new-todo").fill(item_text)
        self.page.locator("input.new-todo").press("Enter")

    def is_todo_item_visible(self, item_text: str) -> bool:
        return self.page.locator(f"li:has-text('{item_text}')").is_visible()
