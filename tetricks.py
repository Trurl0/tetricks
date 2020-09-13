

from field import Field, print_occupations
from tetromino import Tetromino

import numpy as np
import cv2
from mss import mss
from PIL import Image
import copy
import time
import win32api, win32con
import threading
import pickle


# area of the screen where the look for the field
bounding_box = {'top': 420, 'left': 60, 'width': 800, 'height': 800}

win32_key_codes = {
    'up_arrow':0x26,
    'down_arrow':0x28,
    'left_arrow':0x25,
    'right_arrow':0x27,
    'backspace':0x08,
    'esc':0x1B,
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


def simulate_keypress(key):
    time.sleep(0.05)
    win32api.keybd_event(win32_key_codes[key], 0,0,0)
    time.sleep(0.01)
    win32api.keybd_event(win32_key_codes[key],0 ,win32con.KEYEVENTF_KEYUP ,0)


def move(tetromino, column, rotation):
    
    # Initial position to calculate input needed to achieve final position
    initial_j = 3
    
    # Very hacky: get initial position based on type and rotations 
    if tetromino.letter == "O":
        initial_j = 4
    elif tetromino.letter == "I":
        if rotation == 1:
            initial_j = 5
        elif rotation == 3:
            initial_j = 3
    # L, J, S, Z and T are similar
    elif rotation == 1:
            initial_j = 4
    
    # print("initial_j: "+str(initial_j))
    
    h_move = column - initial_j
    # print("move: "+str(h_move))
    # print("rotate: "+str(rotation))
    
    # Rotate always right for now
    if rotation == 3:
        simulate_keypress('z')
    else:
        for i in range(rotation):
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
    simulate_keypress('up_arrow')
    
    
def is_new_round(old_next_tetrominos, next_tetrominos):
    # If the "next" list changes it is a new round 
    # Ignoring the case of four equal tetros in succession, is even possible?
    # TODO: If updated due to an error in recognition we may have some trouble
    next_changed = False
    for (old, new) in zip(old_next_tetrominos, next_tetrominos):
        if old != new:
            next_changed = True
    return next_changed


def test():

    # This is the playing field
    field = Field()
    field.occupations = [
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, False, False, False, False, False, False],
                            [False, False, False, False, True,  False, True,  True,   False, False],
                            [False, False, True,  False, True,  True,  True,  True,   True,  True,],
                            [False, True,  True,  True,  True,  True,  True,  True,   True,  True,],
                        ]
        
        
    # Drop a tetro and calculate heuristics
    field_copy = copy.deepcopy(field)
    next_tetromino = Tetromino.create("L")
    
    field_copy.place_tetromino(next_tetromino, field_copy.occupations, 16, 1)
    print_occupations(field_copy.occupations)
    
    print(field_copy.get_heuristics(field_copy.occupations))
                
                
    # Drop a tetro and calculate heuristics
    field_copy = copy.deepcopy(field)
    next_tetromino = Tetromino.create("L")
    next_tetromino.rotate_right()
    next_tetromino.rotate_right()
    
    field_copy.place_tetromino(next_tetromino, field_copy.occupations, 17, 1)
    print_occupations(field_copy.occupations)
    
    print(field_copy.get_heuristics(field_copy.occupations))
             
def save_calibration(field):

    with open('calibration.pkl', 'wb') as f:
        pickle.dump(field,f)

def load_calibration():

    with open('calibration.pkl', 'rb') as f:
        field = pickle.load(f)
        
        # Reset runtime variables
        field.holes = 0
        
        # Reset occupations
        for i in range(20):
            field.occupations.append([None, None, None, None, None, None, None, None, None, None])
        
    return field
    
def play():

    
    debug = True
    calibrate_from_file = True
    
    # Control flags
    global calibrated
    calibrated = None
    started = False


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
        global calibrated
        while True:
            # Capture image
            img_array = np.array(screenshot.grab(bounding_box))
            
            if debug and calibrated:
                # Show field debug lines
                debug_img = copy.deepcopy(img_array)
                field.debug_playing_area(debug_img)
                cv2.imshow('screen', debug_img)
            else:
                # Show raw image
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
            # Calibrate once
            if not calibrated:
            
                if calibrate_from_file:
                    field = load_calibration()
                    calibrated = True
                else:
                    calibrated = field.detect_playing_area(img_array)
                    save_calibration(field)
                print ("Calibration ok")
                
            else:
                # Update "Next" list
                old_next_tetrominos = copy.deepcopy(next_tetrominos)
                next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
                
                if not started:
                    
                    # Hold first piece, start playing with the next
                    simulate_keypress("c")
                    
                    # Update next list
                    old_next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
                    
                    started = True
                    
                elif is_new_round(old_next_tetrominos, next_tetrominos):
                    
                    # Time to update occupations
                    time.sleep(1.1)
                    time.sleep(0.1)
                    
                    if debug: print("\n\nNEW ROUND\n")
                        
                    # Get occupations, ignoring floating tetros
                    field.get_occupations_from_screen(img_array)
                    if debug: print("Initial occupations")
                    if debug: print_occupations(field.occupations)
                    
                    # Current tetro is first from "Next" list of previous round
                    next_tetromino = Tetromino.create(old_next_tetrominos[0])
                    
                    # Create tetro from "Hold"
                    hold_tetromino = Tetromino.create(hold_tetro)
                    
                    if debug: print("current tetro: "+str(old_next_tetrominos[0]))
                    if debug: print("hold tetro   : "+str(hold_tetro))
                    if debug: print("Next: "+str(next_tetrominos))

                    # Calculate best drop with current and hold
                    score,      best_column, best_rotation, best_occupations= field.calculate_best_drop(next_tetromino)
                    hold_score, hold_column, hold_rotation, hold_occupations = field.calculate_best_drop(hold_tetromino)
                    
                    # Move tetro to best drop, this takes some time due to input delay
                    if hold_score > score:
                        if debug: print_occupations(hold_occupations)
                        simulate_keypress("c")
                        move(hold_tetromino, hold_column, hold_rotation)
                    else:
                        if debug: print_occupations(best_occupations)
                        move(next_tetromino, best_column, best_rotation)
                    # if debug: print("Best column, rotation: "+str(best_column)+", "+str(best_rotation))
                    
                    
                    # pause after moving
                    # simulate_keypress("p")
                
        # except Exception as e:
            # print(str(type(e))+" "+str(e))
            # # break
            
            # # Have we lost, retry?
            # calibrated = False
            
            # # Press new game
            # time.sleep(2)
            # simulate_keypress("z")
            # # Skip adds
            # time.sleep(5)
            # for i in range(2):
                # simulate_keypress("p")
                # time.sleep(2)
                # simulate_keypress("esc")
            # time.sleep(5)
            

if __name__=="__main__":

    play()
    # test()