from time import time
from copy import deepcopy

class Move():
    def __init__(self, y0, x0, y1, x1, piece="--", piece_capt="--", paso=False, enroc=False, check=False, promotion=False):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.piece = piece
        self.piece_capt = piece_capt

        self.paso = paso
        self.promotion = promotion
        self.enroc = enroc
        self.check = check

    def __eq__(self, *args):
        return (self.x0, self.y0, self.x1, self.y1, self.piece)


class GameState():
    def __init__(self):
        self.board = [["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                      ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
                      ["--", "--", "--", "--", "--", "--", "--", "--"],
                      ["--", "--", "--", "--", "--", "--", "--", "--"],
                      ["--", "--", "--", "--", "--", "--", "--", "--"],
                      ["--", "--", "--", "--", "--", "--", "--", "--"],
                      ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
                      ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]

        # Vars to control the castling
        self.w_l_enroc = 0
        self.w_r_enroc = 0
        self.b_l_enroc = 0
        self.b_r_enroc = 0

        #Other pieces vars
        self.blocked_pawns = 0

        # Var to control the player's turn
        self.isWhiteTurn = True

        # Vars to control the game state
        self.theresCheck = False
        self.theresCheckMate = False
        self.theresDraw = False

        # Vars to keep track of the legal moves
        self.legal_moves = []
        self.other_moves = []
        self.ant_move = ""
        self.move_log = []
        self.moves_undoded = []
        
        #Calculate the first legal moves
        self.calc_legal_moves()


    def calc_legal_moves(self):
        """
        * It calculates the legal moves of the current player (self.isWhiteTurn)
        * It stores the value in the list self.legal_moves
        """
        self.legal_moves = []

        # Calculate all the possible moves for the current player
        for i in range(8):
            for j, piece in enumerate(self.board[i]):
                if piece == "--":
                    continue
                elif piece[1] == "p":
                    self.legal_moves += self.pawns_movement(True, i, j, piece)
                elif piece[1] == "N":
                    self.legal_moves += self.knight_movement(True, i, j, piece)
                elif piece[1] == "R":
                    self.legal_moves += self.r_b_Q_movements("R", (1, -1, 0, 0), (0, 0, 1, -1), True, i, j, piece)
                elif piece[1] == "B":
                    self.legal_moves += self.r_b_Q_movements("B", (1, -1, 1, -1), (1, -1, -1, 1), True, i, j, piece)
                elif piece[1] == "Q":
                    self.legal_moves += self.r_b_Q_movements("Q", (1, -1, 0, 0), (0, 0, 1, -1), True, i, j, piece)
                    self.legal_moves += self.r_b_Q_movements("Q", (1, -1, 1, -1), (1, -1, -1, 1), True, i, j, piece)
            
        self.isWhiteTurn = not self.isWhiteTurn
        self.calc_others_legal_moves() #Calculate all the squares where the opponent can capture
        current_other_moves = deepcopy(self.other_moves)
        self.isWhiteTurn = not self.isWhiteTurn

        # Make sure there's no illegal move
        self.legal_moves += self.check_king_movement(self.other_moves)
        king_pos, p = self.calc_kings_position(False)
        self.check_check(self.other_moves, king_pos, p)

        #Del moves that are suited by check
        to_del = []
        for i, move in enumerate(self.legal_moves):
            if (move.y0 == king_pos[0] or move.x0 == king_pos[1]) or abs(move.y0-king_pos[0]) == abs(move.x0-king_pos[1]) or self.theresCheck:
                self.makeMove(move, flag=False)
                self.calc_others_legal_moves()
                if move.piece[1] == "K":
                    king_pos, p = self.calc_kings_position(True)
                self.check_check(self.other_moves, king_pos, p)
                if self.theresCheck:
                    to_del.append(i)
                self.undoMove(flag=False)
                if move.piece[1] == "K":
                    king_pos, p = self.calc_kings_position(False)
                self.other_moves = current_other_moves
                self.check_check(self.other_moves, king_pos, p)

        for i, j in enumerate(to_del):
            del self.legal_moves[-i+j]
        
        # Check checks
        self.other_moves = current_other_moves
        king_pos, p = self.calc_kings_position(False)
        self.check_check(self.other_moves, king_pos, p)

        self.check_checkMate()
        self.check_draw()

    def calc_others_legal_moves(self):
        """
        * It calculates the legal moves of the other player (not self.isWhiteTurn)
        * It stores the value in the list self.other_moves
        """
        self.other_moves = []
        for i in range(8):
            for j, piece in enumerate(self.board[i]):
                if piece == "--":
                    continue
                elif piece[1] == "p":
                    self.other_moves += self.pawns_movement(False, i, j, piece)
                elif piece[1] == "N":
                    self.other_moves += self.knight_movement(False, i, j, piece)
                elif piece[1] == "R":
                    self.other_moves += self.r_b_Q_movements("R", (1, -1, 0, 0), (0, 0, 1, -1), False, i, j, piece)
                elif piece[1] == "B":
                    self.other_moves += self.r_b_Q_movements("B", (1, -1, 1, -1), (1, -1, -1, 1), False, i, j, piece)
                elif piece[1] == "Q":
                    self.other_moves += self.r_b_Q_movements("Q", (1, -1, 0, 0), (0, 0, 1, -1), False, i, j, piece)
                    self.other_moves += self.r_b_Q_movements("Q", (1, -1, 1, -1), (1, -1, -1, 1), False, i, j, piece)
        self.other_moves += self.king_movement(False)


    def makeMove(self, move:Move, undoing=False, flag=True, engine=False):
        """
        It performs the move, updating all the variables that are crucial to update
        * The flag is used to control wether the program should recalculate the legal moves or not
        * The flag also is used to know whether the movement was done by the player or the chessRules module
        * Undoing is set to True if the player is un_undoing the move
        """
        piece = self.board[move.y0][move.x0]
        piece_capt = self.board[move.y1][move.x1]
        move.piece = piece
        move.piece_capt = piece_capt
        self.board[move.y0][move.x0] = "--"
        self.board[move.y1][move.x1] = piece

        move.check = self.theresCheck
        
        move.promotion = self.promotion()


        if move.paso:
            dir_ = 1 if self.isWhiteTurn else -1
            self.board[move.y1+dir_][move.x1] = "--"


        if move.enroc:
            dir_ = 3 if move.enroc=="l" else -2
            posx = 0 if move.enroc=="l" else 7
            posy = 7 if self.isWhiteTurn else 0
            p = "w" if self.isWhiteTurn else "b"
            self.board[posy][posx] = "--"
            self.board[posy][posx+dir_] = p + "R"
    
        self.check_enroc(False, move)


        self.ant_move = move
        if flag or engine:
            self.move_log.append(self.ant_move)

        if not undoing and flag:
            self.moves_undoded = []


        self.theresCheck = False
        self.isWhiteTurn = not self.isWhiteTurn


        if flag:
            self.calc_legal_moves()

    def undoMove(self, flag=True, engine=False, *args):
        
        if len(self.move_log) > 0 or flag==False:
            """
            It performs all the logic to undo the move, updating all the variables that are crucial to update
            * The flag is used to control wether the program should recalculate the legal moves or not
            * The flag also is used to know whether the movement was done by the player or the chessRules module
            """
            if flag:
                move:Move = self.move_log[-1]
            else:
                move:Move = self.ant_move

            self.board[move.y1][move.x1] = move.piece_capt
            self.board[move.y0][move.x0] = move.piece


            if move.paso:
                p = "b" if move.piece[0]=="w" else "w"
                dir_ = 1 if p=="b" else -1
                self.board[move.y1+dir_][move.x1] = p+"p"


            if move.enroc:
                dir_ = 1 if move.enroc=="l" else -1
                posx = 0 if move.enroc=="l" else 7
                posy = 7 if move.piece[0]=="w" else 0
                p = "w" if move.piece[0]=="w" else "b"
                self.board[posy][posx] = p + "R"
                self.board[posy][move.x1+dir_] = "--"

            self.check_enroc(True, move)


            if flag or engine:
                self.moves_undoded.append(move)
                del self.move_log[-1]


            self.theresCheck = False
            self.theresCheckMate = False
            self.theresDraw = False
            self.isWhiteTurn = not self.isWhiteTurn


            if flag:
                self.calc_legal_moves()

    def un_undoMove(self):
        """
        To un_undo the move.
        It calls the makeMove method.
        """
        if len(self.moves_undoded) > 0:
            self.makeMove(self.moves_undoded[-1], undoing=True)
            del self.moves_undoded[-1]


    def pawns_movement(self, flag, i, j, piece):
        """
        It computes the pawn's movement and returns them (a list of 'Move')
        * Flag: It is used to determine wheter the pawns are used by the player or to check that the other is not doing check.
        """
        p = "w" if self.isWhiteTurn else "b" #Define the player
        c = "b" if p == "w" else "w"
        dirs = -1 if p=="w" else 1
        pos_0 = 6 if p=="w" else 1
        paso = 3 if p=="w" else 4

        movements = []

        if piece == p+"p":
            
            if flag:
                self.blocked_pawns = 0

                if self.board[i + dirs][j] == "--": #Move 1 forward
                    movements.append(Move(i, j, i+dirs, j, p+"p"))

                    if i == pos_0:
                        if self.board[i + 2*dirs][j] == "--": #Move 2 forawrd
                            movements.append(Move(i, j, i+2*dirs, j, p+"p"))

                else: #If it can't avamce
                    self.blocked_pawns += 1

                if i == paso and abs(self.move_log[-1].x1 - j)==1 and self.move_log[-1].piece[1] == "p" and self.move_log[-1].y0==7-pos_0 and self.move_log[-1].y1==paso:
                    movements.append(Move(i, j, i+dirs, self.move_log[-1].x1, p+"p", paso=True)) #Check 'en passant'

                if 0 <= i+dirs <= 7 and 0 <= j+1 <= 7:
                    if self.board[i+dirs][j+1][0] == c: #Capture right
                        movements.append(Move(i, j, i+dirs, j+1, p+"p"))
                if 0 <= i+dirs <= 7 and 0 <= j-1 <= 7:
                    if self.board[i+dirs][j-1][0] == c: #Capture left
                        movements.append(Move(i, j, i+dirs, j-1, p+"p"))

            else:
                if 0 <= i+dirs <= 7 and 0 <= j+1 <= 7:
                    movements.append(Move(i, j, i+dirs, j+1, p+"p", self.board[i+dirs][j+1])) #Defend Right
                if 0 <= i+dirs <= 7 and 0 <= j-1 <= 7:
                    movements.append(Move(i, j, i+dirs, j-1, p+"p", self.board[i+dirs][j-1])) #Defend left

        return movements

    def promotion(self):
        """
        If there's a pawn in the last line, change it by a Queen
        """
        for j in range(8):
            if self.board[0][j] == "wp":
                self.board[0][j] = "wQ"
                return True
            if self.board[7][j] == "bp":
                self.board[7][j] = "bQ"
                return True

        return False

    def r_b_Q_movements(self, a_piece, dirx, diry, flag, i, j, piece):
        """
        It computes the rock's, bishop's and queen's movement and returns them (a list of 'Move')
        * a_piece: If the piece we want to compute the move is a R | B | Q
        * dirx: The directions it can move in the X axis.
        * diry: The directions it can move in the Y axis. The movement is compute with the corresponent direction of the dirx movement.
        * Flag: It is used to determine wheter the pawns are used by the player or to check that the other is not doing check.
        """
        p = "w" if self.isWhiteTurn else "b"
        c = "b" if p == "w" else "w"
        dirx = dirx
        diry = diry

        movements = []

        if flag:

            if piece == p+a_piece:

                for k in range(4):
                    a = "__"
                    b = 1

                    if i+dirx[k]*b>=0 and j+diry[k]*b>=0 and i+dirx[k]*b<=7 and j+diry[k]*b<=7: #Make sure the movement is in the board boundaries
                        a = self.board[i+dirx[k]*b][j+diry[k]*b]

                    while a == "--" or a[0] == c:
                        movements.append(Move(i, j, i+dirx[k]*b, j+diry[k]*b, piece, a))

                        if a[0] == c:
                            break

                        b += 1
                        a = "__"
                        if i+dirx[k]*b>=0 and j+diry[k]*b>=0 and i+dirx[k]*b<=7 and j+diry[k]*b<=7:
                            a = self.board[i+dirx[k]*b][j+diry[k]*b]

            return movements

        else:

            if piece == p+a_piece:

                for k in range(4):
                    a = "__"
                    b = 1

                    if i+dirx[k]*b>=0 and j+diry[k]*b>=0 and i+dirx[k]*b<=7 and j+diry[k]*b<=7:
                        a = self.board[i+dirx[k]*b][j+diry[k]*b]

                    while a != "__":
                        movements.append(Move(i, j, i+dirx[k]*b, j+diry[k]*b, piece, a))

                        if a[0] != "-": #If there's a piece #Changed and to revise kdfg dkfgbkdhfg sfdhgsdkfhbg sdfhbkdfhb xkdhfbvkdfhbvx dfhbv xfhbv xfhdbvx fhvbxf dvdfxjhv x
                            break

                        b += 1
                        a = "__"
                        if i+dirx[k]*b>=0 and j+diry[k]*b>=0 and i+dirx[k]*b<=7 and j+diry[k]*b<=7:
                            a = self.board[i+dirx[k]*b][j+diry[k]*b]

            return movements

    def knight_movement(self, flag, i, j, piece):
        """
        It computes the knight's movement and returns them (a list of 'Move')
        * Flag: It is used to determine wheter the pawns are used by the player or to check that the other is not doing check.
        """
        p = "w" if self.isWhiteTurn else "b"
        c = "b" if p == "w" else "w"
        dirx = (2, -2, 1, -1)

        movements = []
        
        if piece == p+"N":

            for k in dirx:
                a = "__"
                b = 1 if abs(k) == 2 else 2

                if i+b>=0 and j+k>=0 and i+b<=7 and j+k<=7:
                    a = self.board[i+b][j+k]

                    if flag:
                        if a == "--" or a[0] == c:
                            movements.append(Move(i, j, i+b, j+k, p+"N"))
                    else: #Changed and to revise ejrbf skjdhbfvskjxhdfb sjfd
                            movements.append(Move(i, j, i+b, j+k, p+"N", a))

                if i-b>=0 and j+k>=0 and i-b<=7 and j+k<=7:
                    a = self.board[i-b][j+k]

                    if flag:
                        if a == "--" or a[0] == c:
                            movements.append(Move(i, j, i-b, j+k, p+"N"))
                    else:
                            movements.append(Move(i, j, i-b, j+k, p+"N", a))

                    
        return movements

    def king_movement(self, flag):
        """
        It computes the king's movement and returns them (a list of 'Move').
        It doesn’t do the castle logic neither checks check
        * Flag: It is used to determine wheter the pawns are used by the player or to check that the other is not doing check.
        """
        p = "w" if self.isWhiteTurn else "b"
        c = "b" if p == "w" else "w"
        dirx = (1, -1, 0)

        movements = []

        for i in range(8):
            for j, piece in enumerate(self.board[i]):
                if piece == p+"K":

                    for k in dirx:
                        for z in dirx:
                            if abs(z) + abs(k) > 0:
                                a = "__"

                                if 0 <= i+z <= 7 and 0 <= j+k <= 7:
                                    a = self.board[i+z][j+k]

                                    if flag:
                                        if a == "--" or a[0] == c:
                                            movements.append(Move(i, j, i+z, j+k, p+"K"))

                                    else: #arbg sjdrhbgskjgrbskjrgfb skjbfrkzjhsbgfskjzfhbg sjdfbg sjf--<< Changed
                                            movements.append(Move(i, j, i+z, j+k, p+"K"))

        return movements

    def check_enroc(self, undoing, move):
        """
        Checks if it's legal to castle.
        It's called in the makeMove method
        """
        value = 1 if not undoing else -1

        if (move.piece == "bR" and move.x0 == 7) or move.piece == "bK":
            self.b_r_enroc += value
        if( move.piece == "bR" and move.x0 == 0) or move.piece == "bK":
            self.b_l_enroc += value
        if (move.piece == "wR" and move.x0 == 0) or move.piece == "wK":
            self.w_l_enroc += value
        if (move.piece == "wR" and move.x0 == 7) or move.piece == "wK":
            self.w_r_enroc += value

    def enroc(self, other_moves):
        """
        If possible, it appends the castle moves.
        """
        p = "w" if self.isWhiteTurn else "b"
        movements = []
        
        if p == "w":
            self.check_check(other_moves, (7,4), "w")
            if not self.theresCheck:
                if self.w_l_enroc==0 and self.board[7][3]=="--" and self.board[7][2]=="--" and self.board[7][0]=="wR":
                    self.check_check(other_moves, (7,3), "w")
                    if not self.theresCheck:
                        movements.append(Move(7, 4, 7, 2, "wK", enroc="l"))
                if self.w_r_enroc==0 and self.board[7][5]=="--" and self.board[7][6]=="--" and self.board[7][7]=="wR":
                    self.check_check(other_moves, (7,5), "w")
                    if not self.theresCheck:
                        movements.append(Move(7, 4, 7, 6, "wK", enroc="r"))

        if p == "b":
            self.check_check(other_moves, (0,4), "b")
            if not self.theresCheck:
                if self.b_l_enroc==0 and self.board[0][3]=="--" and self.board[0][2]=="--" and self.board[0][0]=="bR":
                    self.check_check(other_moves, (0,3), "b")
                    if not self.theresCheck:
                        movements.append(Move(0, 4, 0, 2, "bK", enroc="l"))
                if self.b_r_enroc==0 and self.board[0][5]=="--" and self.board[0][6]=="--" and self.board[0][7]=="bR":
                    self.check_check(other_moves, (0,5), "b")
                    if not self.theresCheck:
                        movements.append(Move(0, 4, 0, 6, "bK", enroc="r"))

        return movements


    def check_king_movement(self, other_moves):
        """
        It deletes a king movement if a piece can kill it.
        """
        king_movements = self.king_movement(True)
        king_movements += self.enroc(other_moves)

        p = "b" if not self.isWhiteTurn else "w"
        c = "w" if not self.isWhiteTurn else "b"

        to_del = []
        for i, king_move in enumerate(king_movements):
            for move in other_moves:
                if king_move.y1 == move.y1:
                    if king_move.x1 == move.x1:
                        to_del.append(i)
                        break

        for i, j in enumerate(to_del):
            del king_movements[-i+j]

        return king_movements

    def calc_kings_position(self, isTurnInverted):
        """
        It finds the king position and return:
        * A tuple with the position (y, x)
        * The current player
        """
        #Calculate king's position
        if isTurnInverted:
            p = "b" if self.isWhiteTurn else "w"
        else:
            p = "w" if self.isWhiteTurn else "b"

        for y in range(len(self.board)):
            for x in range(len(self.board)):
                if self.board[y][x][0] == p and self.board[y][x][1] == "K":
                    return (y, x), p

    def check_check(self, other_moves, king_pos, p):
        """
        It checks if the king is under check.
        It sets the self.theresCheck bool to True.
        """
        if king_pos:
            for move in other_moves:
                if king_pos[0] == move.y1:
                    if king_pos[1] == move.x1:
                        if move.piece != p+"K":
                            self.theresCheck = True
                            break

    def check_checkMate(self):
        """
        It cheks if there's checkMate.
        It turns the self.tehresCheckMate boolean to True.
        """
        if self.theresCheck and len(self.legal_moves) == 0:
            self.theresCheckMate = True

    def check_draw(self):
        """
        It checks if the position is a draw.
        If yes, it sets the boolean var self.theresDraw to True.
        """
        if len(self.legal_moves) == 0 and not self.theresCheck:
            self.theresDraw = True

        if len(self.move_log) > 9:
            if self.move_log[-1].x0 == self.move_log[-5].x0 == self.move_log[-9].x0:
                if self.move_log[-1].y0 == self.move_log[-5].y0 == self.move_log[-9].y0:
                    if self.move_log[-1].piece == self.move_log[-5].piece == self.move_log[-9].piece:
                        self.theresDraw = True

        if len(self.legal_moves) < 10:
            w = 0
            b = 0
            for i in range(8):
                for j in range(8):
                    if self.board[i][j][0] == "w":
                        w += 1
                    elif self.board[i][j][0] == "b":
                        b += 1

                    if w + b > 2:
                        break
                    
                if w + b > 2:
                    break

            if w + b <= 2:
                self.theresDraw = True


