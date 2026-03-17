#!/usr/bin/env python3
"""
Chess Game — tkinter GUI front-end.
Game logic lives in chess_engine.py.
"""

import tkinter as tk
from tkinter import messagebox
from chess_engine import GameState, PIECES

# ─── Layout constants ─────────────────────────────────────────────────────────
BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_PIXEL = BOARD_SIZE * SQUARE_SIZE

# Colors
LIGHT_SQ      = "#F0D9B5"
DARK_SQ       = "#B58863"
SELECTED_SQ   = "#F6F669"
VALID_DOT     = "#CDD16E"
LAST_MOVE_SQ  = "#A8D8A8"
CHECK_SQ      = "#FF4444"


class ChessApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chess")
        self.root.resizable(False, False)
        self.root.configure(bg="#2C2C2C")

        self.gs = GameState()
        self.selected: tuple | None = None   # (r, c) currently selected square
        self.valid_moves: list = []
        self.game_over = False

        self._build_ui()
        self.draw_board()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg="#2C2C2C", height=44)
        top.pack(fill=tk.X)
        tk.Label(top, text="♟  Chess", font=("Helvetica", 18, "bold"),
                 bg="#2C2C2C", fg="white").pack(side=tk.LEFT, padx=12)

        btn_frame = tk.Frame(top, bg="#2C2C2C")
        btn_frame.pack(side=tk.RIGHT, padx=10)
        for label, cmd, color in [
            ("New Game", self.new_game, "#4CAF50"),
            ("Undo",     self.undo_move, "#2196F3"),
        ]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg=color, fg="white", font=("Helvetica", 11, "bold"),
                      relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=4)

        # Board canvas
        self.canvas = tk.Canvas(self.root,
                                width=BOARD_PIXEL, height=BOARD_PIXEL,
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        # Status bar
        self.status_var = tk.StringVar(value="White's turn")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Helvetica", 13), bg="#2C2C2C", fg="white",
                 pady=6).pack(fill=tk.X)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_board(self):
        self.canvas.delete("all")

        # Find king in check
        check_king = None
        if self.gs.is_in_check(self.gs.turn):
            for r in range(8):
                for c in range(8):
                    if self.gs.board[r][c] == self.gs.turn + 'K':
                        check_king = (r, c)

        valid_set = set(self.valid_moves)
        last = set(self.gs.last_move) if self.gs.last_move else set()

        for r in range(8):
            for c in range(8):
                x, y = c * SQUARE_SIZE, r * SQUARE_SIZE
                # Base square color
                color = LIGHT_SQ if (r + c) % 2 == 0 else DARK_SQ
                if (r, c) in last:
                    color = LAST_MOVE_SQ
                if self.selected == (r, c):
                    color = SELECTED_SQ
                if check_king == (r, c):
                    color = CHECK_SQ

                self.canvas.create_rectangle(
                    x, y, x + SQUARE_SIZE, y + SQUARE_SIZE,
                    fill=color, outline="")

                # Valid move highlight
                if (r, c) in valid_set:
                    if self.gs.board[r][c]:          # capture — ring
                        self.canvas.create_rectangle(
                            x, y, x + SQUARE_SIZE, y + SQUARE_SIZE,
                            fill=color, outline=VALID_DOT, width=4)
                    else:                            # empty — dot
                        cx, cy = x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2
                        rd = SQUARE_SIZE // 7
                        self.canvas.create_oval(
                            cx - rd, cy - rd, cx + rd, cy + rd,
                            fill=VALID_DOT, outline="")

                # Piece glyph
                piece = self.gs.board[r][c]
                if piece and piece in PIECES:
                    fg = "#1a1a1a" if piece[0] == 'w' else "white"
                    self.canvas.create_text(
                        x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2,
                        text=PIECES[piece],
                        font=("Arial", int(SQUARE_SIZE * 0.65)),
                        fill=fg)

        # Rank / file labels
        files = "abcdefgh"
        for i in range(8):
            # rank number — right edge
            self.canvas.create_text(
                BOARD_PIXEL - 5, i * SQUARE_SIZE + 10,
                text=str(8 - i), font=("Helvetica", 9, "bold"),
                fill=DARK_SQ if i % 2 == 0 else LIGHT_SQ, anchor="e")
            # file letter — bottom edge
            self.canvas.create_text(
                i * SQUARE_SIZE + 10, BOARD_PIXEL - 5,
                text=files[i], font=("Helvetica", 9, "bold"),
                fill=LIGHT_SQ if i % 2 == 0 else DARK_SQ, anchor="s")

    # ── User interaction ──────────────────────────────────────────────────────

    def on_click(self, event):
        if self.game_over:
            return
        c, r = event.x // SQUARE_SIZE, event.y // SQUARE_SIZE
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        if self.selected:
            if (r, c) in self.valid_moves:
                self._do_move(self.selected[0], self.selected[1], r, c)
                self.selected = None
                self.valid_moves = []
                return
            elif (self.gs.board[r][c] and
                  self.gs.board[r][c][0] == self.gs.turn and
                  (r, c) != self.selected):
                self.selected = (r, c)
                self.valid_moves = self.gs.legal_moves(r, c)
            else:
                self.selected = None
                self.valid_moves = []
        else:
            if self.gs.board[r][c] and self.gs.board[r][c][0] == self.gs.turn:
                self.selected = (r, c)
                self.valid_moves = self.gs.legal_moves(r, c)

        self.draw_board()

    def _do_move(self, fr, fc, tr, tc):
        piece = self.gs.board[fr][fc]
        promotion = 'Q'
        if piece[1] == 'P' and (tr == 0 or tr == 7):
            promotion = self._ask_promotion(piece[0])
        self.gs.make_move(fr, fc, tr, tc, promotion)
        self._update_status()
        self.draw_board()
        self._check_game_over()

    # ── Promotion dialog ──────────────────────────────────────────────────────

    def _ask_promotion(self, color: str) -> str:
        options = [('Q', 'Queen'), ('R', 'Rook'), ('B', 'Bishop'), ('N', 'Knight')]
        dlg = tk.Toplevel(self.root)
        dlg.title("Pawn Promotion")
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.configure(bg="#2C2C2C")
        tk.Label(dlg, text="Promote pawn to:", bg="#2C2C2C", fg="white",
                 font=("Helvetica", 13, "bold")).pack(pady=10)
        choice = tk.StringVar(value='Q')
        frame = tk.Frame(dlg, bg="#2C2C2C")
        frame.pack(padx=20, pady=5)
        for opt, label in options:
            sym = PIECES[color + opt]
            tk.Radiobutton(frame, text=f"{sym}  {label}",
                           variable=choice, value=opt,
                           bg="#2C2C2C", fg="white", selectcolor="#555",
                           font=("Helvetica", 12),
                           activebackground="#2C2C2C").pack(anchor="w", pady=2)
        tk.Button(dlg, text="OK", command=dlg.destroy,
                  bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                  relief=tk.FLAT, padx=15, pady=4).pack(pady=10)
        self.root.wait_window(dlg)
        return choice.get()

    # ── Game controls ─────────────────────────────────────────────────────────

    def new_game(self):
        self.gs = GameState()
        self.selected = None
        self.valid_moves = []
        self.game_over = False
        self.status_var.set("White's turn")
        self.draw_board()

    def undo_move(self):
        if self.game_over:
            self.game_over = False
        self.gs.undo_last_move()
        self.selected = None
        self.valid_moves = []
        self._update_status()
        self.draw_board()

    def _update_status(self):
        turn_name = "White" if self.gs.turn == 'w' else "Black"
        if self.gs.is_in_check(self.gs.turn):
            self.status_var.set(f"{turn_name}'s turn  —  CHECK!")
        else:
            self.status_var.set(f"{turn_name}'s turn")

    def _check_game_over(self):
        if self.gs.is_checkmate():
            winner = "White" if self.gs.turn == 'b' else "Black"
            self.status_var.set(f"Checkmate!  {winner} wins!")
            self.game_over = True
            messagebox.showinfo("Game Over", f"Checkmate!\n{winner} wins! 🎉")
        elif self.gs.is_stalemate():
            self.status_var.set("Stalemate — Draw")
            self.game_over = True
            messagebox.showinfo("Game Over", "Stalemate!\nThe game is a draw.")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
