from copy import deepcopy
from collections import Counter

from chessRules import GameState, Move

class GameEval():
    def __init__(self, game:GameState):
        self.current_game = game
        self.predicted = deepcopy(game)

        self.pos_evaluation = 0

        self.finishedEvaluation = True

        self.piece_values = {"p":100, "R":500, "N":320, "B":330, "Q":900, "K":20000}

        self.pawns_W_opening = [0,  0,  0,  0,  0,  0,  0,  0,
                                50, 50, 50, 50, 50, 50, 50, 50,
                                10, 10, 20, 30, 30, 20, 10, 10,
                                5,  5, 10, 25, 25, 10,  5,  5,
                                0,  0,  0, 20, 20,  0,  0,  0,
                                5, -5,-10,  0,  0,-10, -5,  5,
                                5, 10, 10,-20,-20, 10, 10,  5,
                                0,  0,  0,  0,  0,  0,  0,  0]

        self.knights_W_opening= [-50,-40,-30,-30,-30,-30,-40,-50,
                                -40,-20,  0,  0,  0,  0,-20,-40,
                                -30,  0, 10, 15, 15, 10,  0,-30,
                                -30,  5, 15, 20, 20, 15,  5,-30,
                                -30,  0, 15, 20, 20, 15,  0,-30,
                                -30,  5, 10, 15, 15, 10,  5,-30,
                                -40,-20,  0,  5,  5,  0,-20,-40,
                                -50,-40,-30,-30,-30,-30,-40,-50]

        self.bishops_W_opening= [-20,-10,-10,-10,-10,-10,-10,-20,
                                -10,  0,  0,  0,  0,  0,  0,-10,
                                -10,  0,  5, 10, 10,  5,  0,-10,
                                -10,  5,  5, 10, 10,  5,  5,-10,
                                -10,  0, 10, 10, 10, 10,  0,-10,
                                -10, 10, 10, 10, 10, 10, 10,-10,
                                -10,  5,  0,  0,  0,  0,  5,-10,
                                -20,-10,-10,-10,-10,-10,-10,-20]

        self.rocks_W_opening = [0,  0,  0,  0,  0,  0,  0,  0,
                                5, 10, 10, 10, 10, 10, 10,  5,
                                -5,  0,  0,  0,  0,  0,  0, -5,
                                -5,  0,  0,  0,  0,  0,  0, -5,
                                -5,  0,  0,  0,  0,  0,  0, -5,
                                -5,  0,  0,  0,  0,  0,  0, -5,
                                -5,  0,  0,  0,  0,  0,  0, -5,
                                0,  0,  0,  5,  5,  0,  0,  0]

        self.queen_W_opening= [-20,-10,-10, -5, -5,-10,-10,-20,
                                -10,  0,  0,  0,  0,  0,  0,-10,
                                -10,  0,  5,  5,  5,  5,  0,-10,
                                -5,  0,  5,  5,  5,  5,  0, -5,
                                0,  0,  5,  5,  5,  5,  0, -5,
                                -10,  5,  5,  5,  5,  5,  0,-10,
                                -10,  0,  5,  0,  0,  0,  0,-10,
                                -20,-10,-10, -5, -5,-10,-10,-20]

        self.king_W_opening= [-30,-40,-40,-50,-50,-40,-40,-30,
                            -30,-40,-40,-50,-50,-40,-40,-30,
                            -30,-40,-40,-50,-50,-40,-40,-30,
                            -30,-40,-40,-50,-50,-40,-40,-30,
                            -20,-30,-30,-40,-40,-30,-30,-20,
                            -10,-20,-20,-20,-20,-20,-20,-10,
                            20, 20,  0,  0,  0,  0, 20, 20,
                            20, 30, 10,  0,  0, 10, 30, 20]

        self.pieces_opening_tables_W = {"p":self.pawns_W_opening, "R":self.rocks_W_opening, 
                                        "N":self.knights_W_opening, "B":self.bishops_W_opening, 
                                        "Q":self.queen_W_opening, "K":self.king_W_opening}


    def eval_position(self, game:GameState):
        self.finishedEvaluation = False

        self.pos_evaluation = self.eval_pos(game)

        self.finishedEvaluation = True

    def eval_pos(self, game:GameState):
        board = game.board

        pos_evaluation = 0

        pawns_pos_W = []
        pawns_pos_B = []

        for i in range(8):
            for j, piece in enumerate(board[i]):
                if piece != "--":
                    pos_evaluation += self.checkMaterial(piece)
                    pos_evaluation += self.checkPiecesPosOpening(piece, i, j)

                    if piece[1] == "p":
                        if piece[0] == "w":
                            pawns_pos_W.append((i, j))
                        else:
                            pawns_pos_B.append((i, j))

        pos_evaluation += self.checkDoubledBlockedIsolated_Pawns(board, pawns_pos_W, pawns_pos_B)
                
        
        return pos_evaluation


    def checkMaterial(self, piece):
        pos_evaluation = 0

        p = 1 if piece[0]=="w" else -1
        pos_evaluation += self.piece_values[piece[1]] * p

        return pos_evaluation

    def checkPiecesPosOpening(self, piece, i, j):
        pos_avaluation = 0
        table = self.pieces_opening_tables_W[piece[1]]
        if piece[0] == "w":
            pos_avaluation += table[i*8 + j]
        elif piece[0] == "b":
            pos_avaluation -= table[(7-i)*8 + j]

        return pos_avaluation

    def checkDoubledBlockedIsolated_Pawns(self, board, pawns_pos_W, pawns_pos_B):
        #pawns_pos_W = list(sorted(pawns_pos_W, key=lambda x: x[0]))

        pos_evaluation = 0
        doubled = 0
        isolated = 0
        blocked = 0

        #Checking_doubled_pawns
        doubled_dict = Counter([y for (y,x) in pawns_pos_W])
        for key, value in doubled_dict.items():
            newValue = value if value > 1 else 0
            doubled += newValue

        doubled_dict = Counter([y for (y,x) in pawns_pos_B])
        for key, value in doubled_dict.items():
            newValue = value if value > 1 else 0
            doubled -= newValue

        #Checking_isolated_pawns
        isolated_dict = Counter([x for (y,x) in pawns_pos_W])
        c_isolated_list = set(x for (y,x) in pawns_pos_W)
        c_isolated_list.add(-1)
        c_isolated_list.add(8)
        for key, value in isolated_dict.items():
            if int(key)-1 in c_isolated_list and int(key)+1 in c_isolated_list:
                continue
            else:
                isolated += 1 * value

        isolated_dict = Counter([x for (y,x) in pawns_pos_B])
        c_isolated_list = set(x for (y,x) in pawns_pos_B)
        c_isolated_list.add(-1)
        c_isolated_list.add(8)
        for key, value in isolated_dict.items():
            if key-1 in c_isolated_list and key+1 in c_isolated_list:
                continue
            else:
                isolated -= 1 * value

        #Checking blocked pawns
        for pawn in pawns_pos_W:
            if board[pawn[0]-1][pawn[1]] != "--":
                blocked += 1

        for pawn in pawns_pos_B:
            if board[pawn[0]+1][pawn[1]] != "--":
                blocked -= 1

        pos_evaluation -= 50 * (doubled + isolated + blocked)

        return pos_evaluation

            


    def get_ordered_moves(self, game:GameState):
        """
        Get legal moves.
        Attempt to sort moves by best to worst.
        Use piece values (and positional gains/losses) to weight captures.
        """
        board = game.board

        #end_game = check_end_game(board) Pending to do itehsdf bjdf jdf fdvs df .--------------------<<<<<<<<<<>>>>>>>>>>
        end_game = False

        def orderer(move):
            return self.move_value(game, move, end_game)

        in_order = sorted(game.legal_moves, key=orderer, reverse=game.isWhiteTurn)
        return list(in_order)

    def move_value(self, game:GameState, move:Move, endgame:bool):
        """
        How good is a move?
        A promotion is great.
        A weaker piece taking a stronger piece is good.
        A stronger piece taking a weaker piece is bad.
        Also consider the position change via piece-square table.
        """
        board = game.board
        
        if move.promotion:
            return float("inf") if game.isWhiteTurn else -float("inf")

        _piece = board[move.y0][move.x0]
        position_change = 0
        if _piece != "--":
            _from_value = self.evaluate_piece(_piece, (move.x0,move.y0), endgame)
            _to_value = self.evaluate_piece(_piece, (move.x1,move.y1), endgame)
            position_change = _to_value - _from_value
        else:
            raise Exception(f"A piece was expected at {move.from_square}")

        capture_value = 0.0
        if move.piece_capt != "--":
            capture_value = self.evaluate_capture(game, move)

        current_move_value = capture_value + position_change
        if game.isWhiteTurn == False:
            current_move_value = -current_move_value

        return current_move_value

    def evaluate_piece(self, piece:str, square:tuple, end_game:bool):
        if piece == "--":
            return 0
        else:
            mapping = []
            mapping = self.pieces_opening_tables_W[piece[1]]
            # use end game piece-square tables if neither side has a queen --------To upgrade --------------------<<<<<<<<<<<<<
            ''' if end_game:
                mapping = (
                    kingEvalEndGameWhite
                    if piece.color == chess.WHITE
                    else kingEvalEndGameBlack
                )
            else:
                mapping = kingEvalWhite if piece.color == chess.WHITE else kingEvalBlack '''

            if piece[0] == "w":
                return mapping[square[1]*8 + square[0]]
            else:
                return mapping[(7-square[1])*8 + square[0]]

    def evaluate_capture(self, game:GameState, move:Move):
        """
        Given a capturing move, weight the trade being made.
        """
        board = game.board

        if move.paso:
            return self.piece_values["p"]
        _to = (move.x1, move.y1)
        _from = (move.x0, move.y0)
        if _to is None or _from is None:
            raise Exception(
                f"Pieces were expected at _both_ {(move.x1, move.y1)} and {(move.x0, move.y0)}"
            )
        return self.piece_values[move.piece_capt[1]] - self.piece_values[move.piece[1]]


    #def check_end_game(game:GameState): #To edit asfh skrjgfkjjjgkjsgd kfjhgsd kjg fdkjgshd kfjgsd kfjhsdfkjsdk 
        """
        Are we in the end game?
        Per Michniewski:
        - Both sides have no queens or
        - Every side which has a queen has additionally no other pieces or one minorpiece maximum.
        """
        queens = 0
        minors = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.QUEEN:
                queens += 1
            if piece and (
                piece.piece_type == chess.BISHOP or piece.piece_type == chess.KNIGHT
            ):
                minors += 1

        if queens == 0 or (queens == 2 and minors <= 1):
            return True

        return False
#Towefks hlsrhflskrjf imporve erkj gbshbg sg   s---<<<<<<<<<>>>>>>>>>>---------
