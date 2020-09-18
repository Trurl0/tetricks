

from field import Field, print_occupations
from tetromino import Tetromino

import numpy as np
import cv2
from mss import mss
from PIL import Image
import copy
import time
import win32api, win32con, win32gui
import threading
import pickle


# area of the screen where the look for the field
# Important to start on 0 so screen coordinates match click coordinates, else correct them
bounding_box = {'top': 0, 'left': 0, 'width': 800, 'height': 1300}

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


def simulate_keypress(key, key_delay=0.03):
    win32api.keybd_event(win32_key_codes[key], 0,0,0)
    time.sleep(key_delay)
    win32api.keybd_event(win32_key_codes[key],0 ,win32con.KEYEVENTF_KEYUP ,0)
    time.sleep(key_delay)


def move(tetromino, column, rotation, key_delay=0.3):
    
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
        simulate_keypress('z', key_delay)
    else:
        for i in range(rotation):
            simulate_keypress('x', key_delay)
        
    # Send keypresses with some delay and hard fall at the end
    move_key = "right_arrow"
    if h_move < 0:
        move_key = "left_arrow"
        h_move = -h_move
    for i in range(h_move):
        # print(move_key+" "+str(i))
        simulate_keypress(move_key, key_delay)

    # Hard fall at the end
    simulate_keypress('up_arrow', key_delay)
    
    
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
           
def play():

    # Runtime config
    debug = True
    key_press_delay = 0.028
    # key_press_delay = 0.1
    
    # None if you want to calibrate for a new field
    # calibration = None
    # royale
    calibration = ((154, 318), (569, 1186), (70, 413), [(652, 414), (656, 502), (652, 593)])
    # single player
    # calibration = ((150, 288), (576, 1172), (69, 388), [(659, 390), (659, 478), (659, 570)])

    # Control flags
    global calibrated
    calibrated         = False
    started            = False
    last_cleared_lines = 0
    next_occupations = None


    # To take screenshots
    screenshot = mss()

    # This is the playing field
    field = Field()
    
    # Start with random next tetrominos
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
    
    # To have time to click tetris window
    time.sleep(1)

    if not calibrated:
    
        if calibration is None:
            calibration = field.calibrate_manually(img_array)
            print(calibration)
        
        calibrated = field.set_playing_area(*calibration)
        
        print ("Calibrated")
    
    round_time = time.time()
    while True:
            # continue
        
        try:
            # Update "Next" list to see if is next round
            old_next_tetrominos = copy.deepcopy(next_tetrominos)
            next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
            
            if not started:
                started = True
                
                # Hold first piece, start playing with the next
                simulate_keypress("c")
                
                # Update next list
                old_next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
                
            elif is_new_round(old_next_tetrominos, next_tetrominos):
                print("round_time: "+str(time.time()-round_time))
                round_time = time.time()
                
                # Time to update occupations
                time.sleep(0.08)
                
                if debug: print("\n\nNEW ROUND\n")
                    
                # Hack: when clearing lines the text messes with occupation detection
                # In that case, use calculated ocupations for the next round
                if last_cleared_lines:
                    field.occupations = copy.deepcopy(next_occupations)
                else:
                    # Get occupations, ignoring floating tetros
                    field.get_occupations_from_screen(img_array)
                    
                if debug: print("Initial occupations")
                if debug: print_occupations(field.occupations)
                
                # Current tetro is first from "Next" list of previous round
                next_tetromino = Tetromino.create(old_next_tetrominos[0])
                
                # Create tetro from "Hold"
                if hold_tetro:
                    hold_tetromino = Tetromino.create(hold_tetro)
                
                if debug: print("")
                if debug: print("current tetro: "+str(old_next_tetrominos[0]))
                if debug: print("hold tetro   : "+str(hold_tetro))
                if debug: print("Next: "+str(next_tetrominos))

                # Calculate best drop with current
                score, best_column, best_rotation, best_occupations,\
                holes_score, avg_height_score, height_diff_score,\
                placed_height_score, cleared_lines\
                = field.calculate_best_drop(next_tetromino)
                
                # Calculate best drop with hold
                hold_score, hold_column, hold_rotation, hold_occupations,\
                hold_holes_score, hold_avg_height_score, hold_height_diff_score,\
                hold_placed_height_score, hold_cleared_lines\
                = field.calculate_best_drop(hold_tetromino)
                
                # Move tetro to best drop, current or hold
                if score > hold_score:
                
                    move(next_tetromino, best_column, best_rotation, key_press_delay)
                        
                    last_cleared_lines = cleared_lines
                    next_occupations   = best_occupations
                    
                    if debug:
                        print("")
                        print("best_score:          "+str(score))
                        print("holes_score:         "+str(holes_score))
                        print("avg_height_score:    "+str(avg_height_score))
                        print("height_diff_score:   "+str(height_diff_score))
                        print("placed_height_score: "+str(placed_height_score))
                        print("cleared_lines:       "+str(cleared_lines))
                        # print("Best column, rotation: "+str(best_column)+", "+str(best_rotation))
                        print("best_occupations:")
                        print_occupations(best_occupations) 

                else:
                
                    # Change hold
                    simulate_keypress("c")
                    
                    move(hold_tetromino, hold_column, hold_rotation, key_press_delay)
                    
                    last_cleared_lines = hold_cleared_lines
                    next_occupations   = hold_occupations
                    
                    if debug:
                        print("")
                        print("Hold")
                        print("best_score:          "+str(hold_score))
                        print("holes_score:         "+str(hold_holes_score))
                        print("avg_height_score:    "+str(hold_avg_height_score))
                        print("height_diff_score:   "+str(hold_height_diff_score))
                        print("placed_height_score: "+str(hold_placed_height_score))
                        print("cleared_lines:       "+str(hold_cleared_lines))
                        # print("Best column, rotation: "+str(best_column)+", "+str(best_rotation))
                        print("best_occupations:")
                        print_occupations(hold_occupations) 
                
                # pause after moving
                # simulate_keypress("p")
                
        except Exception as e:
            print(str(type(e))+" "+str(e))
            
            # In case of doubt, hard drop
            simulate_keypress("up_arrow")
            
            

if __name__=="__main__":

    play()
    # test()