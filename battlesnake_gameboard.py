#!/usr/bin/env python2

"""
This implementation is incomplete!
We need to add proper collision detection to make it complete.
It can work fine now as a testing suite, but the user will have to
watch for snake death.
"""

import json
from random import randint, choice

import bottle
import requests

class Snake():

    def __init__(self, name, color, taunt, head_url, api_url):
        # Initialize important snake params
        self.name = name
        self.color = color
        self.taunt = taunt
        self.head_url = head_url
        self.score = 0
        self.last_eaten = 1

        self.api_url = api_url

        self.state = 'alive'
        self.coords = []

        self.tail = None
        self.growing = 3
        self.kills = 0

    def move(self, direction):
        # Given the direction to move, calculates a new head
        x, y = (self.coords[0][0], self.coords[0][1])
        new_head = []
        if direction == 'up':
            new_head = [x, y-1]
        elif direction == 'right':
            new_head = [x+1, y]
        elif direction == 'down':
            new_head = [x, y+1]
        elif direction == 'left':
            new_head = [x-1, y]
        else:
            # Snake moves forward
            pass
        # Check to see if the snake should be growing
        if self.growing > 0:
            self.growing -= 1
        if self.growing == 0:
            # If not growing, pop the tail off and record the location
            self.tail = self.coords.pop()
        # Apply the new head
        self.coords.insert(0, new_head)
        print self.coords
        print self.tail

    def kill_snake(self):
        # When it's time to die, set the state, erase any growing state
        self.state = 'dead'
        self.growing = 0
        # Return half the length to apply to the killer snake
        return len(self.coords)/2

class GameBoard():

    # TODO Collision Detection
    # TODO Process moves (generate new positions)
    # TODO Tally score

    def __init__(self, game_id, dimensions=[15, 15]):
        # Initialize important params
        self.snake_length = 1
        self.game_id = game_id
        self.dimensions = dimensions
        self.ai_urls = ['http://127.0.0.1:8080/']
        self.snakes = []
        self.board = []
        self.food = []
        self.turn = 0

    def gen_post_start(self):
        # Generate the JSON to post when beginning the game
        return json.dumps(
            {'game_id' : self.game_id,
            'width' : self.dimensions[0],
            'height' : self.dimensions[1]}
        )

    def start_game(self):
        for url in self.ai_urls:
            # Post the game start to each AI and get the response
            response = requests.post(
                url + 'start',
                self.gen_post_start(),
                headers={'content-type' : 'application/json'}
            )
            # Unpack the JSON
            response = json.loads(response.text)
            # Create a snake with the response the the AI url
            self.create_snake(response, url)

    def end_game(self):
        for url in self.ai_urls:
            # Post the game end to each AI
            requests.post(
                url + 'end',
                json.dumps({'game_id' : self.game_id}),
                headers={'content-type' : 'application/json'}
            )

    def gen_snakes_for_move(self):
        # Generate the snake objects to Post on each call to /move
        snakes = []
        for snake in self.snakes:
            snakes.append(
                {'name' : snake.name,
                 'state' : snake.state,
                 'coords' : snake.coords,
                 'score' : snake.score,
                 'color' : snake.color,
                 'head_url' : snake.head_url,
                 'taunt' : snake.taunt,
                 'last_eaten' : snake.last_eaten}
            )
        return snakes

    def gen_post_move(self):
        # Generate the JSON to post on each call to /move
        return json.dumps(
            {'game_id' : self.game_id,
             'turn' : self.turn,
             'board' : self.board,
             'food' : self.food,
             'snakes' : self.gen_snakes_for_move()}
        )

    def request_moves(self):
        # Count the turn
        self.turn += 1
        for snake in self.snakes:
            if snake.state == 'alive':
                # Ask the alive snakes for a move
                response = requests.post(
                    snake.api_url + 'move',
                    self.gen_post_move(),
                    headers={'content-type' : 'application/json'}
                )
                response = json.loads(response.text)
                # Call each snake and generate new positions
                snake.move(response['move'])
        # Do Collision Detection before drawing new positions
        self.detect_wall_collision()
        # Maybe we should have a list of snakes to kill and only do so just before we draw?
        self.detect_food_collision()
        """
        TODO:
        #self.detect_body_collision()
        #self.detect_head_collision()
        #self.detect_food_collision()
        #self.detect_starvation()
        """
        self.draw_snakes()
        # Generate food every third turn, unless there is 25 food in play
        if self.turn % 3 == 0 and len(self.food) < 25:
            self.add_apple()

    def detect_wall_collision(self):
        """
        The Snake object doesn't know the board size so here we check if
        it moved off the board in it's previous move. Kill it if it did.
        """
        for snake in self.snakes:
            if snake.state == 'alive':
                if (
                    -1 in snake.coords[0] or
                    self.dimensions[0] in snake.coords[0]
                ):
                    snake.kill_snake()

    def detect_food_collision(self):
        """
        The Snake object doesn't know the board size so here we check if
        it moved off the board in it's previous move. Kill it if it did.
        """
        for snake in self.snakes:
            if snake.state == 'alive':
                print snake.coords[0]
                if snake.coords[0] in self.food:
                    self.food.remove(snake.coords[0])
                    snake.growing = 2

    """
    Body and Head collision needs to be rethought in order to allow the snake
    to compare itself to the board AFTER to moves have been posted.
    This allows directly following a tail, which should be allowed.
    Head on head collisions also need work because odd spaced and even spaced
    moves in H on H collisions can produce different results
    e.g. --> ##H H## <-- (Heads end up in same location)
              ##H##
                ^
                |
              Two heads

         --> ##HH## <-- (Heads end up in neck of other snake)
             ##HH##
               ^^
               ||
           rightleft

    Both cases are clearly head on head, but how can we compute that?
    We should resist computing moves one at a time as it could give someone
    an advantage.

    """

    def detect_body_collision(self):
        for snake in self.snakes:
            x, y = (snake.coords[0][0], snake.coords[0][1])
            if snake.state == 'alive':
                if self.board[x][y]['state'] == 'body':
                    length_for_growing = snake.kill_snake()
                    killers_name = self.board[x][y]['snake']
                    for killer in self.snakes:
                        if killers_name in killer.name:
                            killer.growing =+ length_for_growing + 1
                            killer.coords.append(killer.tail)
                            killer.last_eaten = self.turn
                            killer.kills += 1

    def detect_head_collision(self):
        for snake in self.snakes:
            x, y = (snake.coords[0][0], snake.coords[0][1])
            if snake.state == 'alive':
                if self.board[x][y]['state'] == 'head':
                    killers_name = self.board[x][y]['snake']
                    for killer in self.snakes:
                        if killers_name in killer.name:
                            if len(killer.coords) > len(snake.coords):
                                print "Killer lives"
                            elif len(killer.coords) < len(snake.coords):
                                print "Snake lives"
                            else:
                                print "Both Snakes die"
    # Head to head collisions result in the death of the shorter snake (or both if tied).

    def draw_snakes(self):
        for snake in self.snakes:
            # Initialize some handy internal vars to refer to the snake
            headx, heady = (snake.coords[0][0], snake.coords[0][1])
            body1x, body1y = (snake.coords[1][0], snake.coords[1][1])
            if snake.tail:
                tailx, taily = (snake.tail[0], snake.tail[1])
                # If the snake isn't in a growing state, mark the tail empty
                if snake.growing <= 1:
                    self.board[tailx][taily] = {'state' : 'empty'}
            if snake.state == 'alive':
                # Place the new head on the board.
                self.board[headx][heady] = {'state' : 'head',
                                            'snake' : snake.name}
                if len(snake.coords) > 1:
                    # Make sure the snake has a body, and set it on the board.
                    self.board[body1x][body1y] = {'state' : 'body',
                                                  'snake' : snake.name}
            elif snake.state == 'dead':
                for i, pos in enumerate(snake.coords):
                    if i == 0:
                        """
                        Because a dead snake has moved into something else,
                        do not mark it's head space as empty

                        TODO: What about starvation? In that case the head must
                              be marked empty

                        """
                        continue
                    # Erase the snake from the board
                    self.board[pos[0]][pos[1]] = {'state' : 'empty'}

    def add_apple(self):
        # Generate a candidate position for an apple to appear
        candidate = [randint(0, len(self.board)-1), randint(0, len(self.board)-1)]
        while self.board[candidate[0]][candidate[1]]['state'] != 'empty':
            # If you have to generate more, do it here.
            # TODO: is it possible that we could hang here if all spots are occupied?
            candidate = [randint(0, len(self.board)-1), randint(0, len(self.board)-1)]
        # Write it to the board
        self.board[candidate[0]][candidate[1]]['state'] = 'food'
        # Set the apple in the board state list of foods
        self.food.append(candidate)

    def create_snake(self, vitals, api_url):
        # Here we create the snake with the info from the AI
        name = vitals['name']
        color = vitals['color']
        if 'taunt' in vitals:
            taunt = vitals['taunt']
        else:
            taunt = None
        if 'head_url' in vitals:
            head_url = vitals['head_url']
        else:
            head_url = None
        # Call the constructor with params and place it in the board state list
        self.snakes.append(Snake(name, color, taunt, head_url, api_url))

    def make_empty_board(self):
        # Make an empty board of the correct dimensions
        for column in range(0, self.dimensions[0]):
            self.board.append([])
            for row in range(0, self.dimensions[1]):
                self.board[column].append({'state' : 'empty'})

    def init_snakes(self):
        length = self.snake_length
        for snake in self.snakes:
            # Writing the snakes to the board for the first time
            while True:
                # Generate a candidate position
                candidate = [randint(0, self.dimensions[0]-1), randint(0, self.dimensions[1]-1)]
                empty = True
                # Check if there is some free space around the snake
                if self.board[candidate[0]][candidate[1]]['state'] != 'empty':
                    empty = False
                if empty is False:
                    # Use continue to try again if there isn't space
                    continue
                else:
                    # Finally add the snake to the board state
                    snake.coords.append(candidate)
                    self.board[candidate[0]][candidate[1]]['state'] = 'head'
                    self.board[candidate[0]][candidate[1]]['snake'] = snake.name
                    for i in range(0, length - 1):
                        # Generate random body if applicable
                        # If length == 1, this does nothing
                        body = choice(self.return_emptys(self.get_search_area(candidate, 1)))
                        candidate = body
                        snake.coords.append(body)
                        self.board[body[0]][body[1]]['state'] = 'body'
                        self.board[body[0]][body[1]]['snake'] = snake.name
                    break

    def print_board(self):
        # Make a pretty board to print
        pretty_board = []
        for column in range(0, self.dimensions[1]+2):
            pretty_board.append([])
            for row in range(0, self.dimensions[0]+2):
                # If we're on the edge, make a border
                if (column == 0 or
                   column == self.dimensions[1]+1 or
                   row == 0 or
                   row == self.dimensions[0]+1):
                    pretty_board[column].append('*')
                else:
                    # Make the rest empty
                    pretty_board[column].append(' ')

        for x, column in enumerate(self.board):
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

    def return_emptys(self, coords):
        # For a list of coords, return the empty ones.
        emptys = []
        for each in coords:
            if self.board[each[0]][each[1]]['state'] == 'empty':
                emptys.append(each)
        return emptys

    def get_search_area(self, pos, size):
        # For searching [size] moves away from a given position
        size += 1
        search_area = []
        for x in range(1-size, size):
            for y in range (1-size, size):
                if abs(x) + abs(y) < size:
                    search_area.append([abs(x + pos[0]), abs(y + pos[1])])
        # Return the coords in the search area
        return search_area

board = GameBoard('Local Game')
board.start_game()
board.make_empty_board()
board.init_snakes()
while True:
    board.print_board()
    board.request_moves()
board.end_game()
