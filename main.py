import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image, ImageDraw

from chessRules import GameState, Move

from chessEval import GameEval

from chessEngine import ChessEngine

import os
from copy import deepcopy
from math import log
from time import sleep

class Board(tk.Canvas):
    def __init__(self, parent, root, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.root = root

        # Initialize the constants
        self.SQ_size = 64
        self.color_W = "#f0dab5"
        self.color_B = "#b58763"
        self.Frames = 25
        self.S_per_Frame = 0.25 / self.Frames

        # Create the Game State (to perform the legal moves calculations)
        self.gameState = GameState()
        self.gameEval = GameEval(self.gameState)
        self.gameEngine = ChessEngine(self.gameState)

        #Initialize the thermometer, if needed
        self.thermometer = False
        if "thermometer" in kwargs:
            self.thermometer = kwargs.pop("thermometer")

        #Update the thermometer
        self.parent.after(2000, self.updateThermometer)

        #Initialize the engine, if needed
        self.engine = False
        self.engine_UI = []
        self.engine_depth = 1
        self.engine_player = False
        self.engine_plays = False
        if "engine" in kwargs:
            self.engine = kwargs.pop("engine")

            if "engine_depth" in kwargs:
                self.engine_depth = kwargs.pop("engine_depth")

            if "engine_player" in kwargs:
                self.engine_player = kwargs.pop("engine_player")
                if self.engine_player == "White":
                    self.engine_player = True
                    self.engine_plays = True
                elif self.engine_player == "Black":
                    self.engine_player = False
                    self.engine_plays = True

        # Load piece images and store them in a dict
        self.images = {}
        self.loadImages()

        # Draw the board and store every square in a list
        self.images_board = []
        self.drawBoard()

        # Draw the pieces and store every sprite in a list
        self.images_pieces = []
        self.not_reverse_board = True
        self.drawPieces()

        # Initialize variables to keep track of the user clicks
        self.ant_click = ()
        self.pos_click = ()
        self.possibleMoves = []
        
        # Initialize variables for the GUI
        self.pad = self.SQ_size // 6
        self.possible_moves_UI = []
        self.check_UI = []
        self.last_move_UI = []
        self.bind("<Button-1>", self.showMoves)

        # Make the bind to undo moves
        self.bind_all("<Control-Key-z>", self.undoMove)
        self.bind_all("<Control-Key-y>", self.un_undoMove)
            
        #Show best move
        self.parent.after(2000, self.showBestMove)
        self.bestMove = False
        self.calc_next_best_move = True

    def loadImages(self):
        """
        Loads the images of the pieces and stores them in the dict self.images.
        * The key is the name of the piece in the format 'player( w | b ) + piece( p | R | N | B | K | Q )'. Ex: wp | bK.
        * The images should be stored in the format: player+piece.png or .jpg
        """
        for i in os.listdir("Images"):
            image = ImageTk.PhotoImage(Image.open("Images/" + i).resize((self.SQ_size, (self.SQ_size))))
            self.images[i[:2]] = image

    def drawBoard(self):
        """
        It deletes the current board and draws another one.
        The squares are stored in the list self.images_board
        """
        for i in range(len(self.images_board)):  #To delete the actual widgets
            self.delete(self.images_board[i])
        self.images_board = []
        for i in range(8):
            for j in range(8):
                color = self.color_W if (i+j)%2 == 0 else self.color_B
                a = self.create_rectangle(self.SQ_size*i, self.SQ_size*j, self.SQ_size*(i+1), self.SQ_size*(j+1), fill=color)
                self.images_board.append(a)

    def drawPieces(self):
        """
        It deletes the current pieces and redarws the in the new position.
        The pieces widgets are stored in the list self.images_pieces.
        * The board is reversed if the engine plays and is the white pieces, or if two players are playing aganinst each other (stored in self.not_reverse_board)
        """
        self.not_reverse_board = (self.engine_plays and self.engine_player==False) or (not self.engine_plays and self.gameState.isWhiteTurn) or (self.thermometer and not self.engine_plays)

        for i in range(len(self.images_pieces)):  #To delete the actual widgets
            self.delete(self.images_pieces[i])
        self.images_pieces = []
        for row in range(8):
            for col in range(8):

                if self.not_reverse_board:
                    image = self.gameState.board[row][col]
                else:
                    image = self.gameState.board[7-row][7-col]

                if image != "--":
                    a = self.create_image(col*self.SQ_size + self.SQ_size//2, row*self.SQ_size + self.SQ_size//2, image=self.images[image])
                    self.images_pieces.append(a)


    def create_circle(self, x1, y1, **kwargs):
        """
        Used to create the semi-transparent circles to show either:
        * The possible moves (stored in self.possible_moves_UI)
        * If there's check, checkMate or draw (stored in self.check_UI) (It needs the parameter 'check')
        * To show the best move (since the engine point's of view) (stored in self.engine_UI) (It needs the parameter 'engine')
        """
        x2 = (1+x1)*self.SQ_size-self.pad
        y2 = (1+y1)*self.SQ_size-self.pad
        x1 = x1*self.SQ_size+self.pad
        y1 = y1*self.SQ_size+self.pad
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = root.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (x2-x1, y2-y1), (255, 128, 10, 0))

            x, y = image.size

            canvas = ImageDraw.Draw(image)
            canvas.ellipse((0, 0, x, y), fill)

        if "check" in kwargs:
            self.check_UI.append(ImageTk.PhotoImage(image))
            a = self.create_image(x1, y1, image=self.check_UI[-1], anchor='nw')
            self.check_UI.append(a)
        elif "engine" in kwargs:
            self.engine_UI.append(ImageTk.PhotoImage(image))
            a = self.create_image(x1, y1, image=self.engine_UI[-1], anchor='nw')
            self.engine_UI.append(a)
        elif "lastMove" in kwargs:
            self.last_move_UI.append(ImageTk.PhotoImage(image))
            a = self.create_image(x1, y1, image=self.last_move_UI[-1], anchor='nw')
            self.engine_UI.append(a)
        else:
            self.possible_moves_UI.append(ImageTk.PhotoImage(image))
            a = self.create_image(x1, y1, image=self.possible_moves_UI[-1], anchor='nw')
            self.possible_moves_UI.append(a)

    def showMoves(self, event):
        """
        It checks whether the player has clicked for the first or second time and calls the function.
        It only listents for clicks either if the engine is not playing or is the player's turn.
        """
        if not self.engine_plays or (self.gameState.isWhiteTurn != self.engine_player and self.engine_plays): #If it's not the turn of the engine
            if self.ant_click == (): #If there's no piece clicked
                self.askMoves(event) #Show possible moves

            else:
                self.bestMove = False
                self.makeMove(event, flag="makeMove") #Make sure if the move can be make an make it

    #sdbv dfbv dxjfbvxkdfbv xdf >>---<< To revise
    def askMoves(self, event, engine=False, move=0):
        """
        It keeps track of the first click of the player and shows the possible moves.
        These moves are stores in the list self.possibleMoves.
        * If the board is reversed, the y click is artificially changed only if the client clicked
        """
        try:
            if not engine:
                if self.not_reverse_board:
                    self.ant_click = (int(event.x/self.SQ_size), int(event.y/self.SQ_size)) #Keep track of the square clicked
                else:
                    self.ant_click = (7 - int(event.x/self.SQ_size), 7 - int(event.y/self.SQ_size))
            else:
                    self.ant_click = (move.x0, move.y0)

            for move in self.gameState.legal_moves:
                if move.x0 == self.ant_click[0]:
                    if move.y0 == self.ant_click[1]: #If there's a move which starts in the same square where the client clicked
                        if self.not_reverse_board:
                            self.create_circle(move.x1, move.y1, fill="green", alpha=.75) #Show it in the UI
                        else:
                            self.create_circle(7 - move.x1, 7 - move.y1, fill="green", alpha=.75) #Show it in the UI
                        self.possibleMoves.append(move) #Append the move to the possible moves
        except:
            pass

    def makeMove(self, event, flag=False, engine=False, move=0):
        """
        It makes the move if the move is avaible and refreshes the UI.
        If the move is not made, it calls the askMoves method.
        It also says to the engine that the move was maded
        It also shows the last move done, showing it with a circle
        * With the variable self.calc_next_best_move = True
        * If the board is reversed, the y click is artificially changed only if the client clicked
        """
        a = self.gameEval.get_ordered_moves(self.gameState)
        ''' for move in a:
            print(move.piece) '''
        move_to_do = 0
        if flag == "makeMove": #If the user clicked for a second time
            moveMaded = False
            if not engine:
                if self.not_reverse_board:
                    self.pos_click = (int(event.x/64//1), int(event.y/64//1)) #Keep track of the second square clicked
                else:
                    self.pos_click = (7 - int(event.x/64//1), 7 - int(event.y/64//1)) #Keep track of the second square clicked
            else:
                self.askMoves(False, engine=True, move=move)
                self.pos_click = (move.x1, move.y1)

            for move in self.possibleMoves:
                if self.pos_click[0] == move.x1:
                    if self.pos_click[1] == move.y1: #If there's a move which ends in the same square where the client clicked
                        self.gameState.makeMove(move) #Actually make the move
                        moveMaded = True #Keep track that the move is maded
                        move_to_do = deepcopy(self.ant_click + self.pos_click)
                        break

        elif flag == "undoMove": #If the move is undoed
            self.gameState.undoMove()
            moveMaded = True

        elif flag == "un_undoMove": #If the move is un undoed
            self.gameState.un_undoMove()
            moveMaded = True

        # Restart the variables which keep track of the users inputs
        click = move_to_do
        self.ant_click = ()
        self.pos_click = ()
        self.possibleMoves = []
        for i in range(len(self.possible_moves_UI)):
            self.delete(self.possible_moves_UI[i])
        self.possible_moves_UI = []

        if moveMaded:
            self.calc_next_best_move = True
            self.gameEngine.finishedPrediction = True
            self.gameEngine.continue_calculing = False

            for i in range(len(self.engine_UI)): #Stops showing the engine's prediction
                self.delete(self.engine_UI[i])
            self.engine_UI = []
            self.gameEngine.bestMove = False

            for i in range(len(self.check_UI)): #Stops showing check
                self.delete(self.check_UI[i])
            self.check_UI = []

            for i in range(len(self.last_move_UI)):
                self.delete(self.last_move_UI[i])
            self.last_move_UI = []
            
            if flag == "makeMove":
                self.update_UI(click)
                if self.not_reverse_board:
                    self.create_circle(click[0], click[1], fill="light green", alpha=.5, lastMove=True)
                    self.create_circle(click[2], click[3], fill="light green", alpha=.5, lastMove=True)
                else:
                    self.create_circle(7 - click[0], 7-click[1], fill="light green", alpha=.5, lastMove=True)
                    self.create_circle(7 - click[2], 7-click[3], fill="light green", alpha=.5, lastMove=True)
            else:
                self.drawBoard()
                self.drawPieces()

            if self.gameState.theresCheck: #Show check
                p = "w" if self.gameState.isWhiteTurn else "b"
                for i in range(8):
                    for j in range(8):
                        if self.gameState.board[i][j] == p+"K":
                            if self.not_reverse_board:
                                self.create_circle(j, i, fill="red", alpha=0.55, check=True)
                            else:
                                self.create_circle(7-j, 7-i, fill="red", alpha=0.55, check=True)

                if self.gameState.theresCheckMate: #Show chaeckMate and player who has lost
                    for i in range(8):
                        for j in range(8):
                            if self.gameState.board[i][j][0] == p:
                                if self.not_reverse_board:
                                    self.create_circle(j, i, fill="red", alpha=0.55, check=True)
                                else:
                                    self.create_circle(7-j, 7-i, fill="red", alpha=0.55, check=True)
                    self.gameState.legal_moves = []

            elif self.gameState.theresDraw: #Show draw
                for i in range(8):
                    for j in range(8):
                        if self.gameState.board[i][j] != "--":
                            self.create_circle(j, i, fill="yellow", alpha=0.55, check=True)
                self.gameState.legal_moves = []

        else: #If the move was not made
            self.askMoves(event)

    def undoMove(self, *args):
        """
        It uses the makeMove method to undo the move.
        """
        self.makeMove(False, flag="undoMove")

    def un_undoMove(self, *args):
        """
        It uses the makeMove method to un_undo the move.
        """
        self.makeMove(False, "un_undoMove")

    def update_UI(self, click):
        """
        Given a move, it shows a smoothly, real movement of the piece.
        """
        for img in self.images_pieces:
            x0, y0 = self.coords(img)
            x0 //= self.SQ_size
            y0 //= self.SQ_size
            x0 = int(x0) if self.not_reverse_board else 7 - int(x0)
            y0 = int(y0) if self.not_reverse_board else 7 - int(y0)
            if x0==click[0] and y0==click[1]:
                distx = (click[2] - x0) / self.Frames * self.SQ_size
                disty = (click[3] - y0) / self.Frames * self.SQ_size
                disty = disty if self.not_reverse_board else -disty
                distx = distx if self.not_reverse_board else -distx

                for i in range(self.Frames):
                    self.move(img, distx, disty)
                    self.parent.update_idletasks()
                    sleep(self.S_per_Frame)

                self.drawPieces()
                break


    def updateThermometer(self):
        if self.thermometer and not self.engine:
            if self.gameEval.finishedEvaluation:
                self.gameEval.eval_position(self.gameState)

            self.thermometer.drawScore(-self.gameEval.pos_evaluation*0.5)
            self.root.after(2000, self.updateThermometer)

        elif self.thermometer and self.engine:
            self.thermometer.drawScore(-self.gameEngine.pos_evaluation*0.5)
            self.root.update_idletasks()

    def updateEngine(self, maxDepth, currentDepth):
        if self.engine:
            if maxDepth > 0:
                self.engine.showGame(maxDepth, currentDepth)
                self.root.update_idletasks()

    def showBestMove(self):
        """
        Need to be called first
        * sfbvxdf 
        """
        if self.engine:
            if (self.gameState.isWhiteTurn == self.engine_player and self.engine_plays) or not self.engine_plays: #If it's the turn of the engine or is not playing, then compute
                #self.updateEngine(self.gameEngine.max_games, self.gameEngine.current_eval_game)
                if isinstance(self.gameEngine.bestMove, Move):
                    if self.gameEngine.bestMove in self.gameState.legal_moves and not self.engine_plays:
                        self.create_circle(self.gameEngine.bestMove.x0, self.gameEngine.bestMove.y0, fill="light blue", alpha=.75, engine=True)
                        self.create_circle(self.gameEngine.bestMove.x1, self.gameEngine.bestMove.y1, fill="dark blue", alpha=.75, engine=True)
                        print(self.gameEngine.pos_evaluation)
                if self.gameEngine.bestMove and self.gameEngine.finishedPrediction and self.engine_plays:
                        self.makeMove(False, 'makeMove', True, move=self.gameEngine.bestMove)
                if self.gameEngine.finishedPrediction and self.calc_next_best_move and ((self.engine_plays and self.gameState.isWhiteTurn == self.engine_player) or not self.engine_plays):
                    self.updateThermometer()
                    self.calc_next_best_move = False
                    white = True if len(self.gameState.move_log) % 2 == 0 else False
                    if self.engine_depth == 1:
                        try:
                            depth = round(log(2**14, len(self.gameState.legal_moves))) if round(log(2**14, len(self.gameState.legal_moves)))<=4 else 4
                            print(depth)
                            self.gameEngine.minimax_root(depth, self.gameState)
                        except ZeroDivisionError:
                            depth = 4
                            print(str(depth) + ".")
                            self.gameEngine.minimax_root(depth, self.gameState)
                    else:
                        self.gameEngine.minimax_root(self.engine_depth, self.gameState)

            self.gameEngine.continue_calculing = True
            self.root.after(1000, self.showBestMove)


class Thermometer(tk.Canvas):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.parent = parent
        self.root = root

    def init(self):
        self.SQ_size = self.board.SQ_size
        self.color_W = self.board.color_W
        self.color_B = self.board.color_B

        self.config(width=self.SQ_size//4, height=self.SQ_size*8)
        self.drawScore(0)

    def drawScore(self, num):
        self.delete("all")
        height = self.SQ_size*8
        width = self.SQ_size//4
        for i in range(1001):
            if i == 500:
                self.create_rectangle(0, i*height/1002, width, (i+1)*height/1002, fill="red", outline="red")
            elif i < 500+num:
                self.create_rectangle(0, i*height/1002, width, (i+1)*height/1002, fill="#333333", outline="#333333")
            elif i > 500+num:
                self.create_rectangle(0, i*height/1002, width, (i+1)*height/1002, fill="#BBBBBB", outline="#BBBBBB")
        self.root.update_idletasks()
        
    def add_board(self, board):
        self.board = board
        self.init()

class Engine(tk.Canvas):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.parent = parent
        self.root = root

    def init(self):
        self.SQ_size = self.board.SQ_size
        self.config(height=self.SQ_size//4, width=self.SQ_size*8, bg="red")

    def showGame(self, max_games, current_game):
        self.delete("all")
        width = self.SQ_size*8
        height = self.SQ_size//4
        self.create_rectangle(0, 0, (current_game+1)*width/max_games, height, fill="blue", outline="blue")
        
    def add_board(self, board):
        self.board = board
        self.init()


class Chess(tk.Frame):
    def __init__(self, parent, **kwargs):
        thermometer_needed = False
        engine_needed = False
        engine_depth = 0
        self.engine_player = None

        if "thermometer" in kwargs:
            #Check if the thermometer is needed
            thermometer_needed = kwargs.pop("thermometer")

        if "engine" in kwargs:
            #Check if the engine is needed
            engine_needed = kwargs.pop("engine")
        if "engine_depth" in kwargs:
            engine_depth = kwargs.pop("engine_depth")
        if "engine_player" in kwargs:
            if kwargs["engine_player"] == "White":
                self.engine_player = kwargs.pop("engine_player")
            elif kwargs["engine_player"] == "Black":
                self.engine_player = kwargs.pop("engine_player")


        super().__init__(parent)
        self.parent = parent

        self.thermometer = False
        self.engine = False

        if thermometer_needed:
            #Initialise the thermometer
            self.thermometer = Thermometer(self, self.parent)
            self.thermometer.pack(side="right", anchor="w")

        if engine_needed:
            #Initialise the engine
            self.engine = Engine(self.parent, self.parent)
            self.engine.pack(side="bottom", anchor="center")

        #Initialise the board
        self.board = Board(self, self.parent, thermometer=self.thermometer, engine=self.engine, engine_depth=int(engine_depth), engine_player=self.engine_player)
        self.board.pack(fill="both", expand=True, side="left", anchor="e")

        if thermometer_needed:
            #Link the thermometer with the board
            self.thermometer.add_board(self.board)
        if engine_needed:
            #Link the engine with the board
            self.engine.add_board(self.board)


if __name__ == '__main__':
    window_to_chose = tk.Tk()
    window_to_chose.title("Choose game parameters")

    thermometer = tk.BooleanVar()
    engine = tk.BooleanVar()
    engine_depth = tk.StringVar(value="1")
    engine_player = tk.StringVar()

    def validateNumber(*args):
        try:
            a = int(engine_depth.get())
            if a > 16:
                engine_depth.set(engine_depth.get()[:-1])
            if a == 0:
                engine_depth.set("1")
        except:
            engine_depth.set(engine_depth.get()[:-1])
            if len(engine_depth.get()) == 0:
                engine_depth.set("1")
    engine_depth.trace("w", validateNumber)

    thermometer_check = tk.Checkbutton(window_to_chose, text="Show thermometer", font=("arial", 20), variable=thermometer, onvalue=True, offvalue=False)
    thermometer_check.grid(column=5, row=5, padx=3, pady=5)
    engine_check = tk.Checkbutton(window_to_chose, text="Initiate engine", font=("arial", 20), variable=engine, onvalue=True, offvalue=False)
    engine_check.grid(column=5, row=6, padx=3, pady=5)
    tk.Label(text="Engine depth:", font=("arial", 20)).grid(column=4, row=7, padx=3, pady=5)
    engine_spin = ttk.Spinbox(window_to_chose, from_=1, to=16, textvariable=engine_depth)
    engine_spin.grid(column=5, row=7, padx=3, pady=5)
    tk.Label(text="Engine is", font=("arial", 20)).grid(column=4, row=8, padx=3, pady=5)
    engine_com = ttk.Combobox(window_to_chose, textvariable=engine_player, font=("arial", 20), width=6)
    engine_com["values"] = ("None", "White", "Black")
    engine_com.grid(column=5, row=8, padx=3, pady=5)
    tk.Label(text="player", font=("arial", 20)).grid(column=6, row=8, padx=3, pady=5)

    window_to_chose.mainloop()


    root = tk.Tk()
    root.title("Chess GUI")

    #board = Chess(root)
    board = Chess(root, thermometer=thermometer.get(), engine=engine.get(), engine_player=engine_player.get(), engine_depth=int(engine_depth.get()))
    board.pack(fill="both", expand=True)

    root.geometry(f"{str(64*8+32)}x{str(64*8+32)}")
    root.resizable(1, 1)
    root.mainloop()


