#!/usr/bin/env python3
"""
Chess Game — tkinter GUI front-end.
Game logic lives in chess_engine.py.
Human plays White, Computer plays Black.
"""

import tkinter as tk
from tkinter import messagebox
import random
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

# AI settings
HUMAN_COLOR    = 'w'
COMPUTER_COLOR = 'b'
AI_DEPTH       = 3

# Piece values for evaluation
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from white's perspective, row 0 = rank 8)
PST = {
    'P': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [ 5,  5, 10, 25, 25, 10,  5,  5],
        [ 0,  0,  0, 20, 20,  0,  0,  0],
        [ 5, -5,-10,  0,  0,-10, -5,  5],
        [ 5, 10, 10,-20,-20, 10, 10,  5],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    'R': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [ 5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [ 0,  0,  0,  5,  5,  0,  0,  0],
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    'K': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20],
    ],
}


def evaluate(gs: GameState) -> int:
    """Static board evaluation (positive = good for Black/computer)."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if not piece:
                continue
            col, kind = piece[0], piece[1]
            val = PIECE_VALUES[kind]
            # piece-square bonus
            if col == 'w':
                pst_val = PST[kind][r][c]
                score -= val + pst_val
            else:
                pst_val = PST[kind][7 - r][c]
                score += val + pst_val
    return score


def minimax(gs: GameState, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    if depth == 0:
        return evaluate(gs)
    if gs.is_checkmate():
        return -30000 if maximizing else 30000
    if gs.is_stalemate():
        return 0

    col = COMPUTER_COLOR if maximizing else HUMAN_COLOR
    moves = gs.all_legal_moves(col)
    random.shuffle(moves)   # add variety at equal scores

    if maximizing:
        best = -99999
        for (fr, fc), (tr, tc) in moves:
            gs.make_move(fr, fc, tr, tc)
            best = max(best, minimax(gs, depth - 1, alpha, beta, False))
            gs.undo_last_move()
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 99999
        for (fr, fc), (tr, tc) in moves:
            gs.make_move(fr, fc, tr, tc)
            best = min(best, minimax(gs, depth - 1, alpha, beta, True))
            gs.undo_last_move()
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def best_ai_move(gs: GameState):
    """Return the best (from, to) move for the computer."""
    moves = gs.all_legal_moves(COMPUTER_COLOR)
    if not moves:
        return None
    random.shuffle(moves)
    best_score = -99999
    best_move = moves[0]
    for (fr, fc), (tr, tc) in moves:
        gs.make_move(fr, fc, tr, tc)
        score = minimax(gs, AI_DEPTH - 1, -99999, 99999, False)
        gs.undo_last_move()
        if score > best_score:
            best_score = score
            best_move = ((fr, fc), (tr, tc))
    return best_move


class ChessApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chess  —  You (White) vs Computer (Black)")
        self.root.resizable(False, False)
        self.root.configure(bg="#2C2C2C")

        self.gs = GameState()
        self.selected: tuple | None = None
        self.valid_moves: list = []
        self.game_over = False
        self.ai_thinking = False

        self._build_ui()
        self.draw_board()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        top = tk.Frame(self.root, bg="#2C2C2C", height=44)
        top.pack(fill=tk.X)
        tk.Label(top, text="♟  Chess  —  Human (White) vs AI (Black)",
                 font=("Helvetica", 15, "bold"),
                 bg="#2C2C2C", fg="white").pack(side=tk.LEFT, padx=12)

        btn_frame = tk.Frame(top, bg="#2C2C2C")
        btn_frame.pack(side=tk.RIGHT, padx=10)
        for label, cmd, color in [
            ("New Game", self.new_game,   "#4CAF50"),
            ("Undo",     self.undo_move,  "#2196F3"),
        ]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg=color, fg="white", font=("Helvetica", 11, "bold"),
                      relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=4)

        self.canvas = tk.Canvas(self.root,
                                width=BOARD_PIXEL, height=BOARD_PIXEL,
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        self.status_var = tk.StringVar(value="Your turn (White)")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Helvetica", 13), bg="#2C2C2C", fg="white",
                 pady=6).pack(fill=tk.X)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_board(self):
        self.canvas.delete("all")

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

                if (r, c) in valid_set:
                    if self.gs.board[r][c]:
                        self.canvas.create_rectangle(
                            x, y, x + SQUARE_SIZE, y + SQUARE_SIZE,
                            fill=color, outline=VALID_DOT, width=4)
                    else:
                        cx, cy = x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2
                        rd = SQUARE_SIZE // 7
                        self.canvas.create_oval(
                            cx - rd, cy - rd, cx + rd, cy + rd,
                            fill=VALID_DOT, outline="")

                piece = self.gs.board[r][c]
                if piece and piece in PIECES:
                    fg = "#1a1a1a" if piece[0] == 'w' else "white"
                    self.canvas.create_text(
                        x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2,
                        text=PIECES[piece],
                        font=("Arial", int(SQUARE_SIZE * 0.65)),
                        fill=fg)

        files = "abcdefgh"
        for i in range(8):
            self.canvas.create_text(
                BOARD_PIXEL - 5, i * SQUARE_SIZE + 10,
                text=str(8 - i), font=("Helvetica", 9, "bold"),
                fill=DARK_SQ if i % 2 == 0 else LIGHT_SQ, anchor="e")
            self.canvas.create_text(
                i * SQUARE_SIZE + 10, BOARD_PIXEL - 5,
                text=files[i], font=("Helvetica", 9, "bold"),
                fill=LIGHT_SQ if i % 2 == 0 else DARK_SQ, anchor="s")

    # ── User interaction ──────────────────────────────────────────────────────

    def on_click(self, event):
        # Block clicks when game over or AI is thinking or it's not human's turn
        if self.game_over or self.ai_thinking or self.gs.turn != HUMAN_COLOR:
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
        if self._check_game_over():
            return
        # Schedule AI move after a short delay so the board redraws first
        self.ai_thinking = True
        self.status_var.set("Computer is thinking…")
        self.root.after(150, self._ai_move)

    def _ai_move(self):
        move = best_ai_move(self.gs)
        if move is None:
            self.ai_thinking = False
            return
        (fr, fc), (tr, tc) = move
        # AI always promotes to Queen
        self.gs.make_move(fr, fc, tr, tc, 'Q')
        self.ai_thinking = False
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
        self.ai_thinking = False
        self.status_var.set("Your turn (White)")
        self.draw_board()

    def undo_move(self):
        """Undo both the AI's last reply and the human's last move."""
        if self.ai_thinking:
            return
        if self.game_over:
            self.game_over = False
        # Undo AI move then human move
        self.gs.undo_last_move()
        self.gs.undo_last_move()
        self.selected = None
        self.valid_moves = []
        self._update_status()
        self.draw_board()

    def _update_status(self):
        if self.gs.turn == HUMAN_COLOR:
            label = "Your turn (White)"
        else:
            label = "Computer's turn (Black)"
        if self.gs.is_in_check(self.gs.turn):
            label += "  —  CHECK!"
        self.status_var.set(label)

    def _check_game_over(self) -> bool:
        if self.gs.is_checkmate():
            winner = "Computer (Black)" if self.gs.turn == HUMAN_COLOR else "You (White)"
            self.status_var.set(f"Checkmate!  {winner} wins!")
            self.game_over = True
            messagebox.showinfo("Game Over", f"Checkmate!\n{winner} wins! 🎉")
            return True
        elif self.gs.is_stalemate():
            self.status_var.set("Stalemate — Draw")
            self.game_over = True
            messagebox.showinfo("Game Over", "Stalemate!\nThe game is a draw.")
            return True
        return False


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
