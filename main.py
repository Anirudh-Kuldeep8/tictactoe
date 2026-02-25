import math
import socket
import threading
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.clock import Clock

Window.clearcolor = get_color_from_hex("#f0f2f5")

CLR_PRIMARY = get_color_from_hex("#2d3436")
CLR_ACCENT = get_color_from_hex("#0984e3")
CLR_CELL = get_color_from_hex("#dfe6e9")
CLR_CELL_X = get_color_from_hex("#74b9ff")
CLR_CELL_O = get_color_from_hex("#a29bfe")
CLR_WHITE = get_color_from_hex("#ffffff")
CLR_GREEN = get_color_from_hex("#00b894")
CLR_RED = get_color_from_hex("#d63031")


class TicTacToe(GridLayout):
    def __init__(self, status_label, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.spacing = 6
        self.padding = 6
        self.board = [""] * 9
        self.buttons = []
        self.game_over = False
        self.current_turn = "X"
        self.ai_pending_move = None
        self.client_socket = None
        self.server_socket = None
        self.status_label = status_label

        for i in range(9):
            btn = Button(
                font_size=64,
                bold=True,
                color=CLR_PRIMARY,
                background_normal="",
                background_color=CLR_CELL,
            )
            btn.bind(on_press=lambda instance, idx=i: self.on_cell_press(idx))
            self.buttons.append(btn)
            self.add_widget(btn)

        self.start_server()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", 6000))
        self.server_socket.listen(1)
        print("TCP server listening on 0.0.0.0:6000")
        thread = threading.Thread(target=self.accept_client, daemon=True)
        thread.start()

    def accept_client(self):
        while True:
            try:
                self.client_socket, addr = self.server_socket.accept()
                print(f"Client connected: {addr}")
                Clock.schedule_once(lambda dt: self.set_status("Connected", CLR_GREEN))
            except OSError:
                break

    def set_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    def send_move(self, cell_number):
        if self.client_socket:
            try:
                self.client_socket.sendall(f"{cell_number}\n".encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError, OSError):
                self.client_socket = None
                Clock.schedule_once(lambda dt: self.set_status("Not connected", CLR_RED))

    def on_cell_press(self, idx):
        if self.game_over or self.board[idx] != "":
            return

        if self.current_turn == "X":
            self.board[idx] = "X"
            self.buttons[idx].text = "X"
            self.buttons[idx].background_color = CLR_CELL_X
            if self.check_end():
                return
            self.current_turn = "O"
            Clock.schedule_once(lambda dt: self.ai_compute_and_send(), 0.1)

        elif self.current_turn == "O" and self.ai_pending_move is not None:
            if idx != self.ai_pending_move:
                return
            self.board[idx] = "O"
            self.buttons[idx].text = "O"
            self.buttons[idx].background_color = CLR_CELL_O
            self.ai_pending_move = None
            if self.check_end():
                return
            self.current_turn = "X"

    def ai_compute_and_send(self):
        best_score = -math.inf
        best_idx = None
        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "O"
                score = self.minimax(False)
                self.board[i] = ""
                if score > best_score:
                    best_score = score
                    best_idx = i
        if best_idx is not None:
            self.ai_pending_move = best_idx
            self.send_move(best_idx + 1)

    def minimax(self, is_maximizing):
        winner = self.evaluate()
        if winner is not None:
            return winner
        if is_maximizing:
            best = -math.inf
            for i in range(9):
                if self.board[i] == "":
                    self.board[i] = "O"
                    best = max(best, self.minimax(False))
                    self.board[i] = ""
            return best
        else:
            best = math.inf
            for i in range(9):
                if self.board[i] == "":
                    self.board[i] = "X"
                    best = min(best, self.minimax(True))
                    self.board[i] = ""
            return best

    def evaluate(self):
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in wins:
            if self.board[a] == self.board[b] == self.board[c] != "":
                return 1 if self.board[a] == "O" else -1
        if "" not in self.board:
            return 0
        return None

    def check_end(self):
        result = self.evaluate()
        if result is not None:
            self.game_over = True
            if result == -1:
                print("Player X wins!")
                self.show_popup("You Win!", "Player X wins!")
            elif result == 1:
                print("Machine O wins!")
                self.show_popup("Machine Wins!", "Machine O wins!")
            else:
                print("It's a draw!")
                self.show_popup("Draw!", "Nobody wins this round.")
            return True
        return False

    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=15, padding=20)

        msg_label = Label(
            text=message,
            font_size=24,
            bold=True,
            color=CLR_PRIMARY,
            size_hint=(1, 0.6),
        )

        close_btn = Button(
            text="Play Again",
            font_size=20,
            bold=True,
            size_hint=(0.5, 0.35),
            pos_hint={"center_x": 0.5},
            background_normal="",
            background_color=CLR_ACCENT,
            color=CLR_WHITE,
        )

        content.add_widget(msg_label)
        content.add_widget(close_btn)

        popup = Popup(
            title=title,
            title_size=24,
            title_color=CLR_PRIMARY,
            content=content,
            size_hint=(0.7, 0.35),
            auto_dismiss=False,
            background="",
            background_color=(0.95, 0.96, 0.97, 1),
            separator_color=CLR_ACCENT,
        )

        def on_close(instance):
            popup.dismiss()
            self.reset()

        close_btn.bind(on_press=on_close)
        popup.open()

    def reset(self):
        self.board = [""] * 9
        self.game_over = False
        self.current_turn = "X"
        self.ai_pending_move = None
        for btn in self.buttons:
            btn.text = ""
            btn.background_color = CLR_CELL


class TicTacToeApp(App):
    def build(self):
        self.title = "Tic Tac Toe"
        root = BoxLayout(orientation="vertical", padding=20, spacing=12)

        title_label = Label(
            text="[b]TIC  TAC  TOE[/b]",
            markup=True,
            font_size=34,
            color=CLR_PRIMARY,
            size_hint=(1, 0.08),
        )

        self.conn_label = Label(
            text="Not connected",
            font_size=18,
            bold=True,
            color=CLR_RED,
            size_hint=(1, 0.06),
        )

        self.game = TicTacToe(status_label=self.conn_label, size_hint=(1, 0.74))

        reset_btn = Button(
            text="RESET",
            font_size=22,
            bold=True,
            size_hint=(1, 0.12),
            background_normal="",
            background_color=CLR_ACCENT,
            color=CLR_WHITE,
        )
        reset_btn.bind(on_press=lambda x: self.game.reset())

        root.add_widget(title_label)
        root.add_widget(self.conn_label)
        root.add_widget(self.game)
        root.add_widget(reset_btn)
        return root

    def on_stop(self):
        if self.game.client_socket:
            self.game.client_socket.close()
        if self.game.server_socket:
            self.game.server_socket.close()


if __name__ == "__main__":
    TicTacToeApp().run()
