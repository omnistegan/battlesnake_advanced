#!/usr/bin/env python2

import json
import bottle
from copy import deepcopy

class BasicAI():

    """
    This class is here to fulfill the requirements to the server.
    """

    def __init__(self, name, color, head_url=None, taunt=None):
        self.name = name
        self.color = color
        self.board_dimensions = None
        self.game_id = None
        #Optional
        self.head_url = head_url
        self.taunt = taunt

class Decider():

    def __init__(self):
        # The characters considered impassable.
        self.bad_characters = ['*', '#', 'H', 'A']
        self.counter = 0

        """

        These vars were used for tuning an older version of this snake.
        If we could get tunable vars like this again, they could
        be useful for fine tuning.

        self.wall_vars = {'avoid' : 1.0,
                     'distance_penalty' : 1.0,
                     'strength' : 10.0}
        self.snake_vars = {'avoid' : 1.0,
                     'distance_penalty' : 1.0,
                     'strength' : 10.0}
        self.apple_vars = {'avoid' : -1.0,
                     'distance_penalty' : 1.0,
                     'strength' : 10.0}
        self.self_vars = {'avoid' : -1.0,
                     'distance_penalty' : 1.0,
                     'strength' : 10.0}
        self.empty_vars = {'avoid' : -1.0,
                     'distance_penalty' : 1.0,
                     'strength' : 10.0}
        """

    def get_search_area(self, pos, size):
        size += 1
        search_area = []
        for y in range(1-size, size):
            for x in range (1-size, size):
                if abs(y) + abs(x) < size:
                    search_area.append([abs(y + pos[0]), abs(x + pos[1])])
        return search_area

    def get_possible_moves(self, pos, board):
        possibilities = []
        for move in self.get_search_area(pos, 1):
            if board[move[0]][move[1]] not in self.bad_characters:
                possibilities.append(move)
        return possibilities

    def get_border_search_area(self, pos, size):
        border = []
        border.extend(self.get_search_area(pos, size))
        for each in self.get_search_area(pos, size-1):
            border.remove(each)
        return border

    def determine_score(self, pos, board):
        score = 0

        # Here we copy the board and see how far we can move
        board_copy = deepcopy(board)
        board_copy[pos[0]][pos[1]] = '#'
        tree = [ [[pos[0], pos[1]]] ]
        for level in tree:
            for coord in level:
                tree_append = self.get_possible_moves(coord, board_copy)
                for each in tree_append:
                    board_copy[each[0]][each[1]] = '#'
                if tree_append:
                    tree.append(tree_append)

        # Set the score equal to 100x(1/number of moves deep)
        # Lower score is better
        score = (1.0/len(tree))*100
        """
        for i in range(0, len(board_copy)):
            print ''.join(board_copy[i])
        """
        # Subtract score when food appears
        for i, level in enumerate(tree):
            for coord in level:
                if board[coord[0]][coord[1]] == '@':
                    score -= 1.0/(i+1)
        return score


    def rank_moves(self, pos, board):
        scores = []
        # For possible moves, calculate scores.
        for move in self.get_possible_moves(pos, board):
            scores.append([self.determine_score(move, depth, board), move])
        # If all paths are impassable, move a direction to not hang.
        if len(scores) == 0:
            # Base case
            scores.append([0, [0, 0]])
        # Sort the scores, lower is better.
        scores = sorted(scores)
        # return scores
        new_head = scores[0][1]
        # Determine the correct direction to pass to the server
        if pos[0] == new_head[0]:
            if new_head[1] > pos[1]:
                direction = 'down'
            else:
                direction = 'up'
        else:
            if new_head[0] > pos[0]:
                direction = 'right'
            else:
                direction = 'left'
        # Finally, return the direction to move and the new head pos
        return (direction, new_head)

    def return_new_head(self, pos, board):
        self.counter += 1
        # This is the main call to determine a move.
        decision = self.rank_moves(pos, board)
        return decision[0]

ai = BasicAI('Mr. Pickles', '#ff0000')
decider = Decider()

def translate_board(board):
    # Make a pretty board to print
    pretty_board = []
    for column in range(0, len(board)+2):
        pretty_board.append([])
        for row in range(0, len(board[0])+2):
            # If we're on the edge, make a border
            if (column == 0 or
               column == len(board)+1 or
               row == 0 or
               row == len(board[0])+1):
                pretty_board[column].append('*')
            else:
                # Make the rest empty
                pretty_board[column].append(' ')

    for x, column in enumerate(board):
        for y, row in enumerate(column):
            # Check for bodies, heads, and foods
            if row['state'] == 'body':
                pretty_board[x+1][y+1] = '#'
            elif row['state'] == 'head':
                pretty_board[x+1][y+1] = 'H'
            elif row['state'] == 'food':
                pretty_board[x+1][y+1] = '@'
    # Finally print it out
    for i in range(0, len(pretty_board)):
        print ''.join(pretty_board[i])
    return pretty_board

@bottle.post('/start')
def start():
    data = bottle.request.json

    ai.game_id = data['game_id']
    ai.board_dimensions = [data['width'], data['height']]

    response = {
      'name': ai.name,
      'color': ai.color,
      'head_url': ai.head_url,
      'taunt': ai.taunt
    }

    return { k: v for k, v in response.iteritems() if v != None }

@bottle.post('/move')
def move():
    """
    {
      "game_id": "hairy-cheese",
      "turn": 1,
      "board": [
        [<BoardTile>, <BoardTile>, ...],
        [<BoardTile>, <BoardTile>, ...],
        ...
      ],
      "snakes":[<Snake>, <Snake>, ...],
      "food": [[1, 4], [3, 0], [5, 2]]
    }
    """
    data = bottle.request.json
    # Need to get my own head position
    head = [0, 0]
    for snake in data['snakes']:
        if snake['name'] == ai.name:
            head[0] = snake['coords'][0][0]+1
            head[1] = snake['coords'][0][1]+1
    # This is where you return the move you want to make
    return {'move' : decider.return_new_head(head, translate_board(data['board'])), 'taunt' : 'taunt'}

@bottle.post('/end')
def end():
    data = bottle.request.json

# Expose the app to the web
ai_application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(ai_application, host='127.0.0.1', port=8080)
