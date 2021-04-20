import curses

from client.views.view import View


class MenuView(View):
    def __init__(self, controller):
        super().__init__(controller)
        self.title = ""

    def draw(self):
        super().draw()

        if self.title:
            lines = self.title.split('\n')
            cx: int = 100 - max(len(line) for line in lines) // 2
            for dy, line in enumerate(lines):
                self.addstr(2 + dy, cx, line, curses.COLOR_CYAN)

        for w in self.controller.widgets:
            w.draw()

        hover = self.controller.widgets[self.controller.cursor]
        self.addstr(hover.y, hover.x - 2, "*")


class MainMenuView(MenuView):
    pass


class LoginView(MenuView):
    pass


class RegisterView(MenuView):
    pass
