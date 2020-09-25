

from field import Field, print_occupations, drop_tetromino
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
import random


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


def move(h_move, r_move, play_hold, key_delay=0.3, fall=True):
    
    if play_hold:
        simulate_keypress("c", key_delay)
                    
    # Rotate
    if r_move < 0:
        r_move = -r_move
        for i in range(r_move):
            simulate_keypress('z', key_delay)
    else:
        for i in range(r_move):
            simulate_keypress('x', key_delay)
        
    # Send keypresses with some delay and hard fall at the end
    move_key = "right_arrow"
    if h_move < 0:
        move_key = "left_arrow"
        h_move = -h_move
    for i in range(h_move):
        # print(move_key+" "+str(i))
        simulate_keypress(move_key, key_delay)

    if fall:
        # Hard fall at the end
        simulate_keypress('up_arrow', key_delay)
    
    
def drop_current_tetro(fallen_tetro_letter, column, best_r_move, occupations):
    """Correct occupations with falling tetro (create again as original was rotated in calculations)"""
    fallen_tetro = Tetromino.create(fallen_tetro_letter)
    if best_r_move < 0:
        best_r_move = -best_r_move
        for i in range(best_r_move):
            fallen_tetro.rotate_left()
    else:
        for i in range(best_r_move):
            fallen_tetro.rotate_right()
            
    next_occupations, _, _, _ = drop_tetromino(fallen_tetro, column, occupations)
    
    return next_occupations
    

def choose_curent_or_hold(next_letter, hold_letter, field):
    play_hold = False

    # Calculate best drop with current
    score, best_h_move, best_r_move, best_occupations,\
    holes_score, avg_height_score, height_diff_score,\
    placed_height_score, cleared_lines, max_height, column\
    = field.calculate_best_drop(Tetromino.create(next_letter))

    if hold_letter:
        # Calculate best drop with hold
        hold_score, hold_h_move, hold_r_move, hold_occupations,\
        hold_holes_score, hold_avg_height_score, hold_height_diff_score,\
        hold_placed_height_score, hold_cleared_lines, hold_max_height, hold_column\
        = field.calculate_best_drop(Tetromino.create(hold_letter))

        # Play with hold if better
        if hold_score > score:
            play_hold = True
            
            # Change info to hold version 
            next_letter =  hold_letter
            
            score, best_h_move, best_r_move, best_occupations,\
            holes_score, avg_height_score, height_diff_score,\
            placed_height_score, cleared_lines, max_height, column\
            = hold_score, hold_h_move, hold_r_move, hold_occupations,\
            hold_holes_score, hold_avg_height_score, hold_height_diff_score,\
            hold_placed_height_score, hold_cleared_lines, hold_max_height, hold_column
    
    return next_letter, play_hold,\
            score, best_h_move, best_r_move, best_occupations,\
            holes_score, avg_height_score, height_diff_score,\
            placed_height_score, cleared_lines, max_height, column
     
     
def adapt_keypress_speed(max_height):
    key_press_delay = 0
    if max_height > 8:
        key_press_delay = 0.02
    elif max_height > 6:
        key_press_delay = 0.025
    elif max_height > 4:
        key_press_delay = 0.03
    else:
        key_press_delay = 0.08
    return key_press_delay
        
        
def is_new_round(old_next_tetrominos, next_tetrominos):
    # If the "next" list changes it is a new round 
    # Ignoring the case of four equal tetros in succession, is even possible?
    # TODO: If updated due to an error in recognition we may have some trouble
    next_changed = False
    for (old, new) in zip(old_next_tetrominos, next_tetrominos):
        if old != new:
            next_changed = True
    return next_changed


def screen_thread(screenshot, bounding_box, field, debug):
    """Thread to constantly update the screen image"""
    
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
            cv2.moveWindow("screen", 1000,0);
            
            # Save last imgs for replay
            # img_array_history.append(debug_img)
            # if len(img_array_history) > 100:
                # img_array_history.pop(0)
            
        else:
            # Show raw image
            cv2.imshow('screen', img_array)
            cv2.moveWindow("screen", 1000,0);
            
        time.sleep(0.01)
        
        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            cv2.destroyAllWindows()
            break
            
        # Show image
        cv2.imshow('screen', img_array)
        
        
def play_simulation(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
                     height_diff_weight, non_tetris_line_weight, tetris_weight, move_weight):
    """Play without a real board"""

    debug = False

    # This is the playing field
    field = Field(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
                   height_diff_weight, non_tetris_line_weight, tetris_weight, move_weight)
    
    hold_tetro = random.choice(Tetromino.TYPES)
    
    """Tetromino generation is suffle one of each pieces and draw until empty"""
    next_tetros = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
    random.shuffle(next_tetros)
    
    rounds = 0
    game_score = 0
    max_allowed_height = 18 # Reaching this high means death
    while True:
        rounds += 1

        try:
            next_tetromino = next_tetros.pop(0)
        except:
            next_tetros = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
            random.shuffle(next_tetros)
            next_tetromino = next_tetros.pop(0)
        
        # Choose best next move with current or hold
        fallen_tetro_letter, play_hold,\
        score, best_h_move, best_r_move, best_occupations,\
        holes_score, avg_height_score, height_diff_score,\
        placed_height_score, cleared_lines, max_height, column\
         = choose_curent_or_hold(next_tetromino, hold_tetro, field)
        
        if play_hold:
            hold_tetro = next_tetromino
            
        # Updated with calculated occupations
        field.occupations = copy.deepcopy(best_occupations)
        
        # lines score (normally multiplied by level, but no need)
        if   cleared_lines == 1: game_score += 100
        elif cleared_lines == 2: game_score += 300
        elif cleared_lines == 3: game_score += 500
        elif cleared_lines == 4:
            if last_cleared_lines == 4:
                game_score += 1600
            else:
                game_score += 800
        last_cleared_lines = cleared_lines
        
        # Lose condition
        if(max_height > max_allowed_height):
            break
            
        if debug:
            # print("\nROUND "+str(rounds))
            # print("current tetro: "+str(fallen_tetro_letter))
            # print("hold tetro   : "+str(hold_tetro))
            # print("play_hold    : "+str(play_hold))
            # print("Initial occupations")
            # print_occupations(field.occupations)
            # print("best_score:          "+str(score))
            # print("holes_score:         "+str(holes_score))
            # print("avg_height_score:    "+str(avg_height_score))
            # print("height_diff_score:   "+str(height_diff_score))
            # print("placed_height_score: "+str(placed_height_score))
            # print("cleared_lines:       "+str(cleared_lines))
            print_occupations(field.occupations) 
        
    return game_score, rounds 
       
       
def play(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
            height_diff_weight, non_tetris_line_weight, tetris_weight, move_weight):

    # Globals for screen recognition thread
    global calibrated
    global img_array
    # global img_array_history
    # img_array_history = []  # keep last imgs for replay
    
    # Runtime config
    debug = True
    key_press_delay = 0.05
    
    # Control flags
    calibrated         = False
    started            = False
    last_cleared_lines = 0
    next_occupations   = None

    # None to calibrate for a new field
    # calibration = None
    # calibration = ((154, 318), (569, 1186), (70, 413), [(653, 414), (656, 502), (652, 593)])    # royale
    calibration = ((150, 288), (576, 1172), (69, 388), [(659, 390), (659, 478), (659, 570)])  # single player
    
    # This is the playing field
    field = Field(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
                   height_diff_weight, non_tetris_line_weight, tetris_weight, move_weight)
    
    # Start with random next tetrominos
    next_tetrominos     = ["O", "O", "O"]

    # To take screenshots continually
    screenshot = mss()
    img_array = np.array(screenshot.grab(bounding_box))
    img_thread = threading.Thread(target=screen_thread, args=(screenshot, bounding_box, field, debug), daemon=True)
    img_thread.start()
    
    
    # To have time to click tetris window
    time.sleep(1)

    # Manual calibration
    if calibration is None:
        calibration = field.calibrate_manually(img_array)
        print(calibration)

    # Create field recognition array
    calibrated = field.set_playing_area(*calibration)
    print ("Calibrated: "+str(calibrated))

    # PLAY FIRST ROUND
    rounds = 0
    if debug: print("\n\nROUND "+str(rounds))
    
    next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
    old_next_tetrominos = copy.deepcopy(next_tetrominos)
    
    # Hold first tetro, start playing with the next
    simulate_keypress("c", key_press_delay)
    
    # Get real occupations in case we start mid-game
    time.sleep(0.1)
    field.get_occupations_from_screen(img_array)
    
    # Choose best next move with current or hold
    fallen_tetro_letter, play_hold,\
    score, best_h_move, best_r_move, best_occupations,\
    holes_score, avg_height_score, height_diff_score,\
    placed_height_score, cleared_lines, max_height, column\
     = choose_curent_or_hold(next_tetrominos[0], hold_tetro, field)
    
    while True:
        
        # try:
            
            # Update "Next" list continuously to check when is next round
            old_next_tetrominos = copy.deepcopy(next_tetrominos)
            next_tetrominos, hold_tetro = field.get_next_tetrominos(img_array)
            
            if is_new_round(old_next_tetrominos, next_tetrominos) and "Unknown" not in old_next_tetrominos[1]:
                rounds += 1
                if debug: print("\n\nROUND "+str(rounds))
            
                # For each round, start moving the already calculated movement
                # Think the next movement while the current piece is falling in its final position
                # This way no time is lost thinking
                
                # Move tetro to best drop, don't make it fall yet
                move(best_h_move, best_r_move, play_hold, key_press_delay, False)
                             
                # Hack: when clearing lines the text messes with occupation detection
                # In that case, use calculated ocupations for the next round
                if cleared_lines:
                    field.occupations = copy.deepcopy(best_occupations)    
                else:
                    # Get occupations, ignoring floating tetro
                    field.get_occupations_from_screen(img_array)
                    # Correct with fallen tetro
                    field.occupations = drop_current_tetro(fallen_tetro_letter, column, best_r_move, field.occupations)
                
                # Hard drop tetro now
                simulate_keypress('up_arrow', key_press_delay)
                
                # Update hold tetro in case we have used it
                _, hold_tetro = field.get_next_tetrominos(img_array)
            
                # Choose best move with current or hold
                fallen_tetro_letter, play_hold,\
                score, best_h_move, best_r_move, best_occupations,\
                holes_score, avg_height_score, height_diff_score,\
                placed_height_score, cleared_lines, max_height, column\
                 = choose_curent_or_hold(old_next_tetrominos[1], hold_tetro, field)
                
                if debug:
                    print("current tetro: "+str(old_next_tetrominos[0]))
                    print("hold tetro   : "+str(hold_tetro))
                    print("play_hold    : "+str(play_hold))
                    print("Next: "+str(next_tetrominos))
                    # print("Initial occupations")
                    # print_occupations(field.occupations)
                    print("best_score:          "+str(score))
                    print("holes_score:         "+str(holes_score))
                    print("avg_height_score:    "+str(avg_height_score))
                    print("height_diff_score:   "+str(height_diff_score))
                    print("placed_height_score: "+str(placed_height_score))
                    print("cleared_lines:       "+str(cleared_lines))
                    # print("Best column, rotation: "+str(best_column)+", "+str(best_rotation))
                    # print("occupations:")
                    # print_occupations(field.occupations) 
                    # print("best_occupations:")
                    # print_occupations(best_occupations) 
                
                # pause after moving
                # simulate_keypress("p")
                
            elif "Unknown" in old_next_tetrominos[0]:
                print(old_next_tetrominos[0])
                time.sleep(0.1)
                
        # except Exception as e:
            # print(str(type(e))+" "+str(e))
            # time.sleep(0.5)
            
            # Save replay on exit
            # with open('testricks.pkl', 'wb') as f:
                # pickle.dump(img_array_history, f)
            # break
            
            # In case of doubt, hard drop
            # simulate_keypress("up_arrow")
            
            
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
          

def replay():
    with open('testricks.pkl', 'rb') as f:
        mynewlist = pickle.load(f)
    
        counter = 0
        while True:
            
            counter += 1
            if counter > len(mynewlist)-1:
                counter = 0
                
            img_array = mynewlist[counter]
            # Show raw image
            cv2.imshow('screen', img_array)
            
            time.sleep(0.5)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                cv2.destroyAllWindows()
                break
                
                
if __name__=="__main__":
    
    holes_weight           = 80  
    placed_height_weight   = 3   
    max_height_weight      = 0   
    avg_height_weight      = 6   
    height_diff_weight     = 3   
    non_tetris_line_weight = 40  
    tetris_weight          = 1000
    move_weight            = 1   

    # play(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
                    # height_diff_weight,non_tetris_line_weight, tetris_weight, move_weight)
    
    print(play_simulation(holes_weight, placed_height_weight, max_height_weight, avg_height_weight,\
                    height_diff_weight,non_tetris_line_weight, tetris_weight, move_weight))
    
    # replay()
    
    # test()