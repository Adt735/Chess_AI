from time import time
from copy import deepcopy

from numpy import array, where
from random import choice

import concurrent.futures
import background as bg

from chessRules import GameState, Move
from chessEval import GameEval

class ChessEngine():
    def __init__(self, game:GameState):
        """
        this module implement's Tomasz Michniewski's Simplified Evaluation Function
        https://www.chessprogramming.org/Simplified_Evaluation_Function
        """
        self.current_game = game
        self.predicted_game = game

        self.gameEval = GameEval(game)

        self.startedPrediction = False
        self.finishedPrediction = True

        self.initialDepth = 1
        self.currentDepth = 1

        self.moves_predicted = []
        self.moves_predicted_cache = []
        self.moves_predicted_evaluation = []
        self.bestMove = None
        self.pos_evaluation = 0

        self.MATE_SCORE     = 1000000000
        self.MATE_THRESHOLD =  999000000

        self.max_games = 0
        self.current_eval_game = -1

        self.alpha = -float("inf")
        self.beta = float("inf")

    @bg.task
    def minimax_root(self, depth:int, game:GameState):
        """
        What is the highest value move per our evaluation function?
        * White always wants to maximize (and black to minimize)
        * the board score according to evaluate_board()
        """
        self.moves_predicted = []
        self.moves_predicted_evaluation = []

        self.depth = depth
        self.game = game
        self.maximize = game.isWhiteTurn

        self.finishedPrediction = False
        self.continue_calculing = True

        maximize = game.isWhiteTurn
        best_move = -float("inf") if maximize else float("inf")

        #moves = get_ordered_moves(board)
        game = deepcopy(game)
        moves = game.legal_moves
        best_move_found = moves[0]

        self.max_games = len(game.legal_moves) # To show in the UI
        self.current_eval_game = -1

        t0 = time()
        
        ''' with concurrent.futures.ProcessPoolExecutor(max_workers=len(game.legal_moves)) as executor:
            results = executor.map(self.minimax_multiprocess_root, game.legal_moves)
            for result in results:
                self.moves_predicted.append(result[1])
                self.moves_predicted_evaluation.append(result[0]) '''
        with concurrent.futures.ProcessPoolExecutor(max_workers=len(game.legal_moves)) as executor:
            futures = [executor.submit(self.minimax_multiprocess_root, legal_move) for legal_move in game.legal_moves]
            # iterate over all submitted tasks and get results as they are available
            for future in concurrent.futures.as_completed(futures):
                # get the result for the next completed task
                result = future.result() # blocks
                self.moves_predicted.append(result[1])
                self.moves_predicted_evaluation.append(result[0])
        print("Total time: " + str(time() - t0))

        print(self.moves_predicted_evaluation)
        if maximize:
            best_move = max(self.moves_predicted_evaluation)
            arr = array(self.moves_predicted_evaluation)
            best_move_i = choice(list(where(arr == best_move)[0]))
            best_move_found = self.moves_predicted[best_move_i]

        elif not maximize:
            best_move = min(self.moves_predicted_evaluation)
            arr = array(self.moves_predicted_evaluation)
            best_move_i = choice(where(arr == best_move)[0])
            best_move_found = self.moves_predicted[best_move_i]


        self.bestMove = best_move_found
        self.pos_evaluation = best_move

        self.finishedPrediction = True

    def minimax_multiprocess_root(self, move):
        game = deepcopy(self.game)
        game.makeMove(move)
        # Checking if draw can be claimed at this level, because the threefold repetition check
        # can be expensive. This should help the bot avoid a draw if it's not favorable
        # https://python-chess.readthedocs.io/en/latest/core.html#chess.Board.can_claim_draw
        ''' if board.can_claim_draw():
            game_eval = 0.0
        else: '''
        t0 = time()
        game_eval = self.minimax(self.depth - 1, game, -float("inf"), float("inf"), not self.maximize)
        game.undoMove()

        print("Move:" + str(time() - t0))

        return game_eval, move

    def minimax(self, depth:int, game:GameState, alpha:float, beta:float, is_maximising_player:bool):
        """
        Core minimax logic.
        https://en.wikipedia.org/wiki/Minimax
        """
        if game.theresCheckMate:
            # The previous move resulted in checkmate
            return -self.MATE_SCORE if is_maximising_player else self.MATE_SCORE
        # When the game is over and it's not a checkmate it's a draw
        # In this case, don't evaluate. Just return a neutral result: zero
        elif game.theresDraw:    
            return 0

        if depth == 0:
            return self.gameEval.eval_pos(game)

        if is_maximising_player:
            best_move = -float("inf")
            moves = self.gameEval.get_ordered_moves(game)
            #moves = game.legal_moves
            for move in moves:
                game.makeMove(move)
                curr_eval = self.minimax(depth - 1, game, alpha, beta, not is_maximising_player)
                # Each ply after a checkmate is slower, so they get ranked slightly less
                # We want the fastest mate!
                if curr_eval > self.MATE_THRESHOLD:
                    curr_eval -= 1
                elif curr_eval < -self.MATE_THRESHOLD:
                    curr_eval += 1
                best_move = max(best_move, curr_eval)
                game.undoMove()

                alpha = max(alpha, best_move)
                if beta <= alpha:
                    return best_move
            return best_move
            
        else:
            best_move = float("inf")
            moves = self.gameEval.get_ordered_moves(game)
            #moves = game.legal_moves
            for move in moves:
                game.makeMove(move)
                curr_eval = self.minimax(depth - 1, game, alpha, beta, not is_maximising_player)
                if curr_eval > self.MATE_THRESHOLD:
                    curr_eval -= 1
                elif curr_eval < -self.MATE_THRESHOLD:
                    curr_eval += 1
                best_move = min(best_move, curr_eval)
                game.undoMove()

                beta = min(beta, best_move)
                if beta <= alpha:
                    return best_move
            return best_move



