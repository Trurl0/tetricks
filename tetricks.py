

import numpy as np
import cv2
from mss import mss
from PIL import Image
import copy
import time
import win32api, win32con
import threading

# area of the screen where the look for the field
bounding_box = {'top': 420, 'left': 60, 'width': 800, 'height': 800}

# Color constants
background_color  = [73, 26, 12, 255]
next_bounds_color = [255, 255, 255, 255]
T_color  = [178, 100, 140, 255]
I_color  = [228, 225, 177, 255]
Z_color  = [182, 164, 239, 255]
S_color  = [171, 240, 177, 255]
L_color  = [129, 182, 239, 255]
J_color  = [228, 177, 148, 255]
O_color  = [187, 232, 251, 255]

win32_key_codes = {
    'up_arrow':0x26,
    'down_arrow':0x28,
    'left_arrow':0x25,
    'right_arrow':0x27,
    '0':0x30,
    '1':0x31,
    '2':0x32,
    '3':0x33,
    '4':0x34,
    '5':0x35,
    '6':0x36,
    '7':0x37,
    '8':0x38,
    '9':0x39,
    'a':0x41,
    'b':0x42,
    'c':0x43,
    'd':0x44,
    'e':0x45,
    'f':0x46,
    'g':0x47,
    'h':0x48,
    'i':0x49,
    'j':0x4A,
    'k':0x4B,
    'l':0x4C,
    'm':0x4D,
    'n':0x4E,
    'o':0x4F,
    'p':0x50,
    'q':0x51,
    'r':0x52,
    's':0x53,
    't':0x54,
    'u':0x55,
    'v':0x56,
    'w':0x57,
    'x':0x58,
    'y':0x59,
    'z':0x5A,
}

def is_similar_color(color1, color2, tolerance = 3):
    # colors are BGRA, only BGR are important
    is_similar = True
    for i in range(2):
        if not (color1[i] - tolerance < color2[i] < color1[i] + tolerance):
            is_similar = False
            break
    return is_similar
    

class Tetromino:

    TYPES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']

    def __init__(self, body, letter):
        self.body   = body
        self.letter = letter

    @staticmethod
    def ITetromino(letter):
        return Tetromino(
            [
                [1, 1, 1, 1]
            ], letter
        )

    @staticmethod
    def OTetromino(letter):
        return Tetromino(
            [
                [1, 1],
                [1, 1]
            ], letter
        )

    @staticmethod
    def TTetromino(letter):
        return Tetromino(
            [
                [0, 1, 0],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def STetromino(letter):
        return Tetromino(
            [
                [0, 1, 1],
                [1, 1, 0]
            ], letter
        )

    @staticmethod
    def ZTetromino(letter):
        return Tetromino(
            [
                [1, 1, 0],
                [0, 1, 1]
            ], letter
        )

    @staticmethod
    def JTetromino(letter):
        return Tetromino(
            [
                [1, 0, 0],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def LTetromino(letter):
        return Tetromino(
            [
                [0, 0, 1],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def create(letter):
        return getattr(Tetromino, '{}Tetromino'.format(letter.upper()))(letter)

    def __str__(self):
        return "\n".join(["".join(str(x)) for x in self.body])

    def copy(self):
        return Tetromino([row[:] for row in self.body], self.letter)

    def width(self):
        return len(self.body[0])

    def height(self):
        return len(self.body)

    def rotate_right(self):
        self.body = list(zip(*self.body[::-1]))
        return self

    def rotate_left(self):
        self.body = list(reversed(list(zip(*self.body))))
        return self

    def flip(self):
        self.body = [row[::-1] for row in self.body[::-1]]
        return self


class Cell:
    def __init__(self, screen_i, screen_j):
        self.screen_i = screen_i
        self.screen_j = screen_j
            

class Field:
    def __init__(self):
        # Create playing field of 20*10
        self.width  = 10
        self.height = 20
        
        # TODO: calibrate weight for heuristics
        self.higher_weight     = 0
        self.height_avg_weight = 5
        self.holes_weight      = 10
        
        # Create empty list for needed arrays
        self.screen_positions = []        
        for i in range(20):
            self.screen_positions.append([None, None, None, None, None, None, None, None, None, None])
            
        self.occupations = []  
        for i in range(20):
            self.occupations.append([None, None, None, None, None, None, None, None, None, None])
        
    def detect_playing_area(self, img_array, debug=False):
            
        try:
            # All this to be returned
            left_border = None
            right_border = None
            top_border = None
            down_border = None
            next_left_border = None
            next_right_border = None
            next_top_border = None
            next_down_border = None
            
            # Detect vertical borders
            for j in range(0, 800):
                i = 200
                if is_similar_color(img_array[i, j], background_color):
                    if not left_border:
                        left_border = [i, j]
                else:
                    if left_border and not right_border:
                        right_border = [i, j]
                                
            # Detect horizontal borders
            for i in range(0, 800):
                j = left_border[1] + 1
                if is_similar_color(img_array[i, j], background_color):
                    if not top_border:
                        top_border = [i, j]
                else:
                    if top_border and not down_border:
                        down_border = [i, j]
            
            # Get next piece vertical borders
            inside_border = False
            for j in range(right_border[1], 800):
                i = 200
                if is_similar_color(img_array[i, j], next_bounds_color):
                    if not inside_border:
                        inside_border = True
                        if next_left_border and not next_right_border:
                            next_right_border = [i, j]
                else:
                    if inside_border:
                        inside_border = False
                        if not next_left_border:
                            next_left_border = [i, j]
                        
            # Use vertical info for horizontal
            inside_border = False
            for i in range(0, 800):
                j = next_right_border[1]-5
                if is_similar_color(img_array[i, j], next_bounds_color):
                    if not inside_border:
                        inside_border = True
                        if next_top_border and not next_down_border:
                            next_down_border = [i, j]
                else:
                    if inside_border:
                        inside_border = False
                        if not next_top_border:
                            next_top_border = [i, j]
            
            # Aprox cell size 
            cell_size = (down_border[0] - top_border[0]) / 20
            x_offset = cell_size/2 + 5 # To get the aprox center of each cell
            y_offset = cell_size/2 - 5 # To get the aprox center of each cell

            # Assign a screen coordinate to each cell in screen_positions
            # The pixel in each coordinate is used to detect the state of each cell
            for i in range(20):
                for j in range(10):
                    screen_i = int(top_border[0] + (i*cell_size) + x_offset)
                    screen_j = int(left_border[1] + (j*cell_size) + y_offset)
                    self.screen_positions[i][j] = Cell(screen_i, screen_j)
                
            # Get screen coordinate of next pieces
            next_middle = next_left_border[1] + int((next_right_border[1] - next_left_border[1])/2)
            next_offset = int((next_down_border[0] - next_top_border[0])/3)
            self.next_locations = [[int(next_top_border[0]+next_offset*0.6), next_middle],
                              [int(next_top_border[0]+next_offset*1.6), next_middle],
                              [int(next_top_border[0]+next_offset*2.65), next_middle]]
                              
            # For debugging only, careful as we are drawing on the original img
            if debug:
            
                # Draw playing field area
                for i in range(top_border[0], down_border[0]):
                    img_array[i, left_border[1]]  = [0, 255, 0, 255]
                    img_array[i, right_border[1]] = [0, 255, 0, 255]
                for j in range(left_border[1], right_border[1]):
                    img_array[top_border[0], j]  = [0, 255, 0, 255]
                    img_array[down_border[0], j] = [0, 255, 0, 255]
                              
                # Draw next piece area
                for i in range(next_top_border[0], next_down_border[0]):
                    img_array[i, next_left_border[1]]  = [0, 255, 0, 255]
                    img_array[i, next_right_border[1]] = [0, 255, 0, 255]
                for j in range(next_left_border[1], next_right_border[1]):
                    img_array[next_top_border[0], j]  = [0, 255, 0, 255]
                    img_array[next_down_border[0], j] = [0, 255, 0, 255]
                              
                # Draw detection axes
                for i in range(0, 800):
                    j = left_border[1] + 1
                    if top_border[0] < i < down_border[0]:
                        img_array[i, j] = [0, 255, 0, 255]
                    else:
                        img_array[i, j] = [0, 0, 255, 255]
                for j in range(0, 800):
                    i = 200
                    if (left_border[1] < j < right_border[1]) or (next_left_border[1] < j < next_right_border[1]) :
                        img_array[i, j] = [0, 255, 0, 255]
                    else:
                        img_array[i, j] = [0, 0, 255, 255]
                    
                for i in range(0, 800):
                    j = next_right_border[1]-5
                    if next_top_border[0] < i < next_down_border[0]:
                        img_array[i, j] = [0, 255, 0, 255]
                    else:
                        img_array[i, j] = [0, 0, 255, 255]
                        
                for i in range(next_top_border[0], next_down_border[0]):
                    img_array[i, next_middle] = [255, 255, 0, 255]
                    
                for loc in self.next_locations:
                    for i in range(next_middle-20, next_middle+20):
                        img_array[loc[0], i] = [255, 255, 0, 255]
                     
                for i in range(20):
                    for j in range(10):
                        for i2 in range(3):
                            for j2 in range(3):
                               img_array[self.screen_positions[i][j].screen_i+i2, self.screen_positions[i][j].screen_j+j2]  = [255, 0, 255, 255]
            return True
        except Exception as e:
            print("detect_playing_area FAILED")
            print(type(e)+" "+str(e))
            return False
            
    def get_occupations_from_screen(self, img_array):
        
        for i in range(20):
            for j in range(10):
                # print(i, j)
                # print(self.screen_positions[i][j])
                x = self.screen_positions[i][j].screen_i - 1 # Hack: -5 to avoid debug area
                y = self.screen_positions[i][j].screen_j 
                if is_similar_color(img_array[x, y], background_color, 3):
                    self.occupations[i][j] = False
                else:
                    self.occupations[i][j] = True
                    
        # Delete occupations for moving piece (delete all ocupations above first empty line)
        empty_line = None
        
        # Get the first empty line (bottom to top)
        for i in range(19, 0, -1):
            line_is_empty = True
            for j in range(10):
                if self.occupations[i][j]:
                    line_is_empty = False
                    break
            if line_is_empty:
                empty_line = i
                break
                
        # Delete all occupations over it
        if empty_line:
            # print("Delete above line "+str(empty_line))
            for i in range(empty_line, -1, -1):
                # print("Delete line "+str(i))
                for j in range(10):
                    self.occupations[i][j] = False
        return self.occupations
            
    def get_next_tetrominos(self, img_array):
        
        next_tetrominos = []
        for loc in self.next_locations:
            # Hack: +1 to avoid looking at debug lines (always the same color)
            if is_similar_color  (img_array[loc[0]+1, loc[1]+1], T_color, tolerance=10): next_tetrominos.append("T")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], I_color, tolerance=10): next_tetrominos.append("I")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], Z_color, tolerance=10): next_tetrominos.append("Z")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], S_color, tolerance=10): next_tetrominos.append("S")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], L_color, tolerance=10): next_tetrominos.append("L")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], J_color, tolerance=10): next_tetrominos.append("J")
            elif is_similar_color(img_array[loc[0]+1, loc[1]+1], O_color, tolerance=10): next_tetrominos.append("O")
            # else: print("Unknown: "+str(img_array[loc[0]+1, loc[1]+1]))
            
        return next_tetrominos

    def show_debug_field(self, img_array):

        for loc in self.next_locations:
            for i in range(-10, 10):
                img_array[loc[0], loc[1]+i] = [255, 255, 0, 255]
                img_array[loc[0]+i, loc[1]] = [255, 255, 0, 255]
             
    def place_tetromino(self, tetromino, occupations, field_i, field_j):
        # occupy field with tetronimo in definitive position    
        for i, row in enumerate(tetromino.body):
            for j, occupied in enumerate(row):
                if occupied:
                    occupations[i+field_i][j+field_j] = True
              
    def get_height_and_holes(self, occupations):
        # Together to optimize search
    
        # j is column, break column on higher occupation
        higher     = 20
        holes      = 0
        height_sum = 0
        for j in range(10):            
            first_col_occupation = False
            for i in range(20):
                if occupations[i][j]:
                    first_col_occupation = True
                    height_sum += i
                    # print(str(i)+", "+str(j))
                    if i < higher:
                        higher = i
                        # print("HIGHER: "+str(higher))
                        
                elif first_col_occupation:
                    holes += 1
                
        return height_sum/10, higher, holes
    
    def get_heuristics(self, occupations):
        score = 0
        height_avg, higher, holes = self.get_height_and_holes(occupations)
        # print("height: "+str(height))
        # print("holes: "+str(holes))
        score = height_avg*(self.height_avg_weight) + higher*(self.higher_weight) - holes*(self.holes_weight)
        return score, height_avg, higher, holes
            
    def drop_test(self, tetromino, drop_j):

        # Drop a copy of the tetromino on a copy of the field
        test_occupations = copy.deepcopy(self.occupations)
        temp_tetromino = tetromino.copy()
        
        # Drop until floor, keep last valid position
        last_valid_i = 0
        try:
            for drop_i in range(21 - tetromino.height()):
                # print("drop: "+str(drop_i)+", "+str(drop_j))
            
                # Stop at occupation
                for i, row in enumerate(tetromino.body):
                    for j, occupied in enumerate(row):
                        if occupied:
                            # print("Checking "+str(drop_i+i)+", "+str(drop_j+j))
                            if self.occupations[drop_i+i][drop_j+j]:
                                # print("Collision "+str(drop_i)+", "+str(drop_j))
                                
                                raise StopIteration
                                
                # Save only if no collision
                last_valid_i = drop_i
                # continue  
            # break  
        except StopIteration: pass
    
        # place dropped tetro in test board test_occupations
        self.place_tetromino(temp_tetromino, test_occupations, last_valid_i, drop_j)
        
        return test_occupations
        
    def calculate_best_drop(self,tetromino):
        # Assumptions:
        # we have space to move freely all the way
        
        best_column      = 0
        best_rotation    = 0
        best_score       = None
        best_height_sum  = None
        best_higher      = None
        best_holes       = None
        best_occupations = None
        
        # Test drop in every column and rotation
        # print("Testing drop")
        for rotation in range(4):
            # print("rotation "+str(rotation))
            # print("tetromino.width "+str(tetromino.width()))
            # print("range "+str(self.width - tetromino.width()))
            
            for column in range(self.width - tetromino.width() + 1):
                
                test_occupations = self.drop_test(tetromino, column)
                
                # TODO: in copied and modified field, not original one...
                score, height_avg, higher, holes = self.get_heuristics(test_occupations)
                    
                # Keep movement with better heuristics
                if best_score is None or score > best_score:
                    # print("new best: "+str(heuristics)+", col "+str(column)+", rot "+str(rotation))
                    best_score       = score
                    best_column      = column
                    best_rotation    = rotation
                    best_occupations = test_occupations
                    best_height_avg  = height_avg
                    best_higher      = higher
                    best_holes       = holes
                    
            # rotate for next try
            tetromino.rotate_right()
            
        print("")
        print("best_score: "+str(best_score))
        print("holes_score:      "+str(best_holes       *(self.holes_weight)))
        print("height_sum_score: "+str(best_height_avg  *(self.height_avg_weight)))
        print("higher_score:     "+str(best_higher      *(self.higher_weight)))
        # print("best_column: "+str(best_column))
        # print("best_rotation: "+str(best_rotation))
        # print("best_occupations:")
        # print_occupations(best_occupations)
            
        return best_column, best_rotation
                   
    def set_occupations_test(self, occupations):
    
        for i in range(20):
            for j in range(10):            
                self.occupations[i][j] = False
                for occ in occupations:
                    if (i == occ[0]) and (j == occ[1]):
                        self.occupations[i][j] = True
                        
    def print_occupations(self):
        # print to cmd
        for i in range(20):
            print([str(x).replace("True", "X").replace("False", " ") for x in self.occupations[i]])
       
def print_occupations(occupations):
    # print to cmd
    for i in range(20):
        print([str(x).replace("True", "X").replace("False", " ") for x in occupations[i]])


def simulate_keypress(key):
    time.sleep(0.1)
    win32api.keybd_event(win32_key_codes[key], 0,0,0)
    time.sleep(0.01)
    win32api.keybd_event(win32_key_codes[key],0 ,win32con.KEYEVENTF_KEYUP ,0)


def move(tetromino, best_column, best_rotation):
    
    # Initial position to calculate input needed to achieve final position
    initial_j = 3
    
    # Very hacky: get initial position based on type and rotations 
    if tetromino.letter == "O":
        initial_j = 4
    
    elif tetromino.letter == "I":
        if best_rotation == 1:
            initial_j = 5
        elif best_rotation == 3:
            initial_j = 3
            
    # L, J, S, Z and T are similar
    elif best_rotation == 1:
            initial_j = 4
    
    # print("initial_j: "+str(initial_j))
    
    h_move = best_column - initial_j
    # print("move: "+str(h_move))
    # print("rotate: "+str(best_rotation))
    
    # time.sleep(1)
    
    # Rotate always right for now
    for i in range(best_rotation):
        # print("rotate x")
        simulate_keypress('x')
        
    # Send keypresses with some delay and hard fall at the end
    move_key = "right_arrow"
    if h_move < 0:
        move_key = "left_arrow"
        h_move = -h_move
    for i in range(h_move):
        # print(move_key+" "+str(i))
        simulate_keypress(move_key)

    # Hard fall at the end
    # time.sleep(2)
    simulate_keypress('up_arrow')
    

def test():

    # This is the playing field
    field = Field()
        
    test_occupations = [
                                                                                          
                                                          [17, 4],             [17, 6],   [17, 7],
                                      [18, 2],            [18, 4],   [18, 5],  [18, 6],   [18, 7],  [18, 8],   [18, 9],
                            [19, 1],  [19, 2],  [19, 3],  [19, 4],   [19, 5],  [19, 6],   [19, 7],  [19, 8],   [19, 9], 
                        ]
    field.set_occupations_test(test_occupations)
        
        
    # Drop a tetro and calculate heuristics
    field_copy = copy.deepcopy(field)
    next_tetromino = Tetromino.create("L")
    
    field_copy.place_tetromino(next_tetromino, field_copy.occupations, 17, 1)
    field_copy.print_occupations()
    
    print(field_copy.get_heuristics())
                
                
    # Drop a tetro and calculate heuristics
    field_copy = copy.deepcopy(field)
    next_tetromino = Tetromino.create("L")
    next_tetromino.rotate_right()
    next_tetromino.rotate_right()
    
    field_copy.place_tetromino(next_tetromino, field_copy.occupations, 16, 1)
    field_copy.print_occupations()
    
    print(field_copy.get_heuristics())
             
            
def play():

    debug = False
    calibrated = False

    # To take screenshots
    screenshot = mss()

    # This is the playing field
    field = Field()
    
    # Start with a random next tetromino
    next_tetrominos = ["O", "O", "O"]
        
    global img_array
    img_array = np.array(screenshot.grab(bounding_box))
    
    # Thread to constantly update the screen image
    def screen_thread():
        global img_array
        while True:
            # Capture image
            img_array = np.array(screenshot.grab(bounding_box))
            
            # Show image
            cv2.imshow('screen', img_array)
            
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                cv2.destroyAllWindows()
                break
                
            # Show image
            cv2.imshow('screen', img_array)
            
    img_thread = threading.Thread(target=screen_thread, daemon=True)
    img_thread.start()
    
    # To have time to click tetris windows
    time.sleep(1)
    
    while True:
        
        # try:
            # Calibrate once, or manually with key 'c'
            if not calibrated:
                calibrated = field.detect_playing_area(img_array, debug)
                print ("Calibration ok: "+str(calibrated))
                
            else:
                if debug: print("\n\nNEW ROUND\n")
                # Get occupations, ignoring floating tetros
                field.get_occupations_from_screen(img_array)
                if debug: print("Initial occupations")
                if debug: field.print_occupations()
            
                # Current tetro is first from "Next" list of previous round
                next_tetromino = Tetromino.create(next_tetrominos[0])
                if debug: print("current tetro: "+str(next_tetrominos[0]))
                
                # Update "Next" list for next round
                next_tetrominos = field.get_next_tetrominos(img_array)
                if debug: print("Next: "+str(next_tetrominos))

                # Calculate best drop
                best_column, best_rotation = field.calculate_best_drop(next_tetromino)
                if debug: print("Best column, rotation: "+str(best_column)+", "+str(best_rotation))
                
                # Move current tetro to best drop
                # This takes some time due to input delay
                move(next_tetromino, best_column, best_rotation)
                time.sleep(0.4)
                    
                # if debug:
                    # print("DEBUG:")
                    
                    # field.print_occupations()
                    # field.show_debug_field(img_array)
                    
                    # Pause everithing to check
                    # time.sleep(1)
                    # simulate_keypress("p")
                    # input("Press enter Enter and click quickly on tetris window!!")
                    # time.sleep(2)
                    # simulate_keypress("u")
                    # time.sleep(1)
                    
                
        # except Exception as e:
            # calibrated = False
            # print(str(type(e))+" "+str(e))
            # break

if __name__=="__main__":

    play()
    # test()
