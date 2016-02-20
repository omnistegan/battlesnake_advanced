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
        for i, level in enumerate(tree):
            for coord in level:
                if board[coord[0]][coord[1]] == '$':
                    score -= (1.0/(i+1))*1000
        return score

    def rank_moves(self, pos, board, snakes):
        scores = []
        # For possible moves, calculate scores.
        for move in self.get_possible_moves(pos, board):

            # Find where other snakes can move
            if move not in self.other_snake_moves(snakes, board):
                scores.append([self.determine_score(move, board), move])
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
                direction = 'south'
            else:
                direction = 'north'
        else:
            if new_head[0] > pos[0]:
                direction = 'east'
            else:
                direction = 'west'
        # Finally, return the direction to move and the new head pos
        return (direction, new_head)

    def return_new_head(self, pos, board, snakes):
        self.counter += 1
        # This is the main call to determine a move.
        decision = self.rank_moves(pos, board, snakes)
        return decision[0]

    def other_snake_moves(self, snakes, board):
        self.length = 0
        moves = []
        for snake in data['snakes']:
            if snake['name'] = ai.name:
                self.length = len(snake['coords'])
        for snake in data['snakes']:
            if snake['name'] = ai.name:
                pass
            else len(snake['coords']) >= self.length:
                moves.extend(self.get_possible_moves(snake['coords'][0], board))
        return moves


ai = BasicAI('The Mutaneers', '#ff0000')
decider = Decider()

def make_board(data):
    # Make, print, and return an ASCII array.
    pretty_board = []
    for column in range(0, data['width']+2):
        pretty_board.append([])
        for row in range(0, data['height']+2):
            # If we're on the edge, make a border
            if (column == 0 or
               column == data['width']+1 or
               row == 0 or
               row == data['height']+1):
                pretty_board[column].append('*')
            else:
                # Make the rest empty
                pretty_board[column].append(' ')

    # Put snakes and food on the board
    for food in data.get('food'):
        pretty_board[food[0]+1][food[1]+1] = '@'
    for snake in data['snakes']:
        for i, pos in enumerate(snake['coords']):
            if i == 0:
                pretty_board[pos[0]+1][pos[1]+1] = 'H'
            else:
                pretty_board[pos[0]+1][pos[1]+1] = '#'
    # Extra Walls and Coins
    if data['mode'] == 'advanced':
        for wall in data.get('walls'):
            pretty_board[wall[0]+1][wall[1]+1] = '*'
        for coin in data.get('gold'):
            pretty_board[coin[0]+1][coin[1]+1] = '$'

    for i in range(0, len(pretty_board)):
        print ''.join(pretty_board[i])
    return pretty_board

@bottle.post('/start')
def start():
    data = bottle.request.json

    ai.game_id = data['game']
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

    """
    {u'mode': u'classic',
     u'snakes': [{u'taunt': u'WAKAWAKAWAKAWAKAWAKA',
                  u'age': 11,
                  u'name': u'SnacMan',
                  u'health': 98,
                  u'id': u'07a8c99f-1077-4a4e-86bf-a6ba390f8546',
                  u'coords': [[8, 5], [7, 5], [7, 6], [7, 7], [7, 8]],
                  u'status': u'alive',
                  u'kills': 0,
                  u'message': u''},
                 {u'taunt': u'',
                  u'age': 11,
                  u'name': u'The Mutaneers',
                  u'health': 89,
                  u'id': u'039b3cce-ce9e-4263-b568-9dadf9cf6ee5',
                  u'coords': [[0, 3], [1, 3], [2, 3]],
                  u'status': u'alive',
                  u'kills': 0,
                  u'message': u''}],
     u'game': u'limping-nutrition',
     u'turn': 11,
     u'food': [[0, 5], [10, 4]],
     u'width': 15,
     u'height': 15}
    """
    data = bottle.request.json

    # Need to produce a new board.

    # Need to get my own head position
    head = [0, 0]
    for snake in data['snakes']:
        if snake['name'] == ai.name:
            head[0] = snake['coords'][0][0]+1
            head[1] = snake['coords'][0][1]+1
    print head
    # This is where you return the move you want to make
    return {'move' : decider.return_new_head(head, make_board(data), data['snakes']), 'taunt' : 'taunt'}

@bottle.post('/end')
def end():
    data = bottle.request.json
    return {}

@bottle.get('/')
def root():
    return {}

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
