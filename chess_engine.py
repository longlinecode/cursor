"""
Chess engine — pure game logic, no GUI dependencies.
"""

# Unicode chess piece symbols
PIECES = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟',
}


def initial_board():
    board = [[None] * 8 for _ in range(8)]
    order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    for col, p in enumerate(order):
        board[0][col] = 'b' + p
        board[7][col] = 'w' + p
    for col in range(8):
        board[1][col] = 'bP'
        board[6][col] = 'wP'
    return board


class GameState:
    def __init__(self):
        self.board = initial_board()
        self.turn = 'w'
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant_target = None   # (row, col) square capturable en passant
        self.move_log = []              # (fr, fc, tr, tc, captured, promotion)
        self.last_move = None           # ((fr,fc),(tr,tc))

    # ── helpers ──────────────────────────────────────────────

    def get(self, r, c):
        return self.board[r][c]

    def color_at(self, r, c):
        p = self.board[r][c]
        return p[0] if p else None

    @staticmethod
    def enemy(col):
        return 'b' if col == 'w' else 'w'

    # ── pseudo-legal moves (ignores check) ───────────────────

    def pseudo_moves(self, r, c):
        piece = self.board[r][c]
        if not piece:
            return []
        col, kind = piece[0], piece[1]
        moves = []

        def add(tr, tc):
            if 0 <= tr < 8 and 0 <= tc < 8:
                target = self.board[tr][tc]
                if target is None or target[0] != col:
                    moves.append((tr, tc))

        def slide(dr, dc):
            tr, tc = r + dr, c + dc
            while 0 <= tr < 8 and 0 <= tc < 8:
                target = self.board[tr][tc]
                if target is None:
                    moves.append((tr, tc))
                elif target[0] != col:
                    moves.append((tr, tc))
                    break
                else:
                    break
                tr += dr
                tc += dc

        if kind == 'P':
            direction = -1 if col == 'w' else 1
            start_row = 6 if col == 'w' else 1
            tr = r + direction
            if 0 <= tr < 8 and self.board[tr][c] is None:
                moves.append((tr, c))
                tr2 = r + 2 * direction
                if r == start_row and self.board[tr2][c] is None:
                    moves.append((tr2, c))
            for dc in (-1, 1):
                tc = c + dc
                tr = r + direction
                if 0 <= tr < 8 and 0 <= tc < 8:
                    target = self.board[tr][tc]
                    if target and target[0] != col:
                        moves.append((tr, tc))
                    if (tr, tc) == self.en_passant_target:
                        moves.append((tr, tc))

        elif kind == 'N':
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                add(r+dr, c+dc)

        elif kind == 'B':
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                slide(dr, dc)

        elif kind == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                slide(dr, dc)

        elif kind == 'Q':
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
                slide(dr, dc)

        elif kind == 'K':
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                add(r+dr, c+dc)
            row = 7 if col == 'w' else 0
            if r == row and c == 4:
                if (self.castling_rights[col+'K'] and
                        self.board[row][5] is None and self.board[row][6] is None and
                        self.board[row][7] == col+'R'):
                    moves.append((row, 6))
                if (self.castling_rights[col+'Q'] and
                        self.board[row][3] is None and self.board[row][2] is None and
                        self.board[row][1] is None and self.board[row][0] == col+'R'):
                    moves.append((row, 2))
        return moves

    # ── check detection ──────────────────────────────────────

    def _is_square_attacked(self, kr, kc, by_col, board):
        """Return True if square (kr,kc) is attacked by any piece of by_col on board."""
        saved = self.board
        self.board = board
        attacked = False
        for r in range(8):
            for c in range(8):
                if board[r][c] and board[r][c][0] == by_col:
                    for (tr, tc) in self.pseudo_moves(r, c):
                        if (tr, tc) == (kr, kc):
                            attacked = True
                            break
                if attacked:
                    break
            if attacked:
                break
        self.board = saved
        return attacked

    def is_in_check(self, col, board=None):
        if board is None:
            board = self.board
        king_pos = None
        for r in range(8):
            for c in range(8):
                if board[r][c] == col + 'K':
                    king_pos = (r, c)
                    break
        if king_pos is None:
            return False
        return self._is_square_attacked(king_pos[0], king_pos[1], self.enemy(col), board)

    # ── move simulation ──────────────────────────────────────

    def _apply_move(self, fr, fc, tr, tc, board, castling_rights, en_passant_target):
        b = [row[:] for row in board]
        cr = dict(castling_rights)
        piece = b[fr][fc]
        col, kind = piece[0], piece[1]
        ep = None

        # en passant capture
        if kind == 'P' and (tr, tc) == en_passant_target:
            b[fr][tc] = None

        # double pawn push
        if kind == 'P' and abs(tr - fr) == 2:
            ep = ((fr + tr) // 2, tc)

        # castling rook move
        if kind == 'K':
            if fc == 4 and tc == 6:
                b[fr][5] = b[fr][7]
                b[fr][7] = None
            elif fc == 4 and tc == 2:
                b[fr][3] = b[fr][0]
                b[fr][0] = None
            cr[col+'K'] = False
            cr[col+'Q'] = False

        # update castling rights on rook moves / captures
        if kind == 'R':
            if fr == 7 and fc == 0: cr['wQ'] = False
            if fr == 7 and fc == 7: cr['wK'] = False
            if fr == 0 and fc == 0: cr['bQ'] = False
            if fr == 0 and fc == 7: cr['bK'] = False
        if tr == 7 and tc == 0: cr['wQ'] = False
        if tr == 7 and tc == 7: cr['wK'] = False
        if tr == 0 and tc == 0: cr['bQ'] = False
        if tr == 0 and tc == 7: cr['bK'] = False

        b[tr][tc] = piece
        b[fr][fc] = None
        return b, cr, ep

    # ── legal moves ──────────────────────────────────────────

    def legal_moves(self, r, c):
        piece = self.board[r][c]
        if not piece or piece[0] != self.turn:
            return []
        moves = []
        for (tr, tc) in self.pseudo_moves(r, c):
            new_board, new_cr, new_ep = self._apply_move(
                r, c, tr, tc, self.board, self.castling_rights, self.en_passant_target)
            if self.is_in_check(self.turn, new_board):
                continue
            # castling: king must not pass through or start in check
            if piece[1] == 'K' and abs(tc - c) == 2:
                if self.is_in_check(self.turn, self.board):
                    continue
                mid_col = (c + tc) // 2
                mid_board, _, _ = self._apply_move(
                    r, c, r, mid_col, self.board, self.castling_rights, self.en_passant_target)
                if self.is_in_check(self.turn, mid_board):
                    continue
            moves.append((tr, tc))
        return moves

    def all_legal_moves(self, col):
        result = []
        for r in range(8):
            for c in range(8):
                if self.board[r][c] and self.board[r][c][0] == col:
                    for m in self.legal_moves(r, c):
                        result.append(((r, c), m))
        return result

    # ── make move ────────────────────────────────────────────

    def make_move(self, fr, fc, tr, tc, promotion='Q'):
        piece = self.board[fr][fc]
        captured = self.board[tr][tc]
        new_board, new_cr, new_ep = self._apply_move(
            fr, fc, tr, tc, self.board, self.castling_rights, self.en_passant_target)

        # pawn promotion
        promo_piece = None
        if piece[1] == 'P' and (tr == 0 or tr == 7):
            new_board[tr][tc] = piece[0] + promotion
            promo_piece = promotion

        self.board = new_board
        self.castling_rights = new_cr
        self.en_passant_target = new_ep
        self.last_move = ((fr, fc), (tr, tc))
        self.move_log.append((fr, fc, tr, tc, captured, promo_piece))
        self.turn = self.enemy(self.turn)

    def undo_last_move(self):
        """Undo the most recent move (simplified — castling rights not fully restored)."""
        if not self.move_log:
            return
        fr, fc, tr, tc, captured, promo_piece = self.move_log.pop()
        piece = self.board[tr][tc]
        # if promotion happened, restore to pawn
        if promo_piece:
            piece = piece[0] + 'P'
        self.board[fr][fc] = piece
        self.board[tr][tc] = captured
        self.turn = self.enemy(self.turn)
        self.last_move = None
        self.en_passant_target = None

    # ── game-over checks ─────────────────────────────────────

    def is_checkmate(self):
        return self.is_in_check(self.turn) and len(self.all_legal_moves(self.turn)) == 0

    def is_stalemate(self):
        return not self.is_in_check(self.turn) and len(self.all_legal_moves(self.turn)) == 0
