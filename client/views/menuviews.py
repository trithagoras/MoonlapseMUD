import curses

from client.views.view import View


class MenuView(View):
    def __init__(self, controller):
        super().__init__(controller)
        self.title = ""

    def draw(self):
        super().draw()

        if self.title:
            self.addstr(2, (100 - len(self.title)) // 2, self.title, curses.COLOR_CYAN)

        for w in self.controller.widgets:
            w.draw()

        hover = self.controller.widgets[self.controller.cursor]
        self.addstr(hover.y, hover.x - 1, "*")


class MainMenuView(MenuView):
    pass


class LoginView(MenuView):
    pass


class RegisterView(MenuView):
    pass
