

import numpy as np
import cv2
from mss import mss
from PIL import Image

bounding_box = {'top': 420, 'left': 60, 'width': 800, 'height': 800}

screenshot = mss()

# Color constants
background_color  = [73, 26, 12, 255]
next_bounds_color = [255, 255, 255, 255]
T_color  = [178, 100, 140, 255]
I_color  = [228, 225, 177, 255]
z_color  = [182, 164, 239, 255]
z2_color = [172, 243, 179, 255]
L_color  = [129, 182, 239, 255]
L2_color = [228, 177, 148, 255]
o_color  = [187, 232, 251, 255]

def is_similar_color(color1, color2, tolerance = 3):
    # colors are BGRA, only BGR are important
    is_similar = True
    for i in range(2):
        if not (color1[i] - tolerance < color2[i] < color1[i] + tolerance):
            is_similar = False
            break
    return is_similar

class Cell:
    def __init__(self, screen_i, screen_j):
        self.screen_i = screen_i
        self.screen_j = screen_j
        self.occupied = False  # only fixed pieces occupy cells
            
def detect_borders(img_array, debug=False):
        
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
        i = 100
        if is_similar_color(img_array[i, j], background_color):
        # if (img_array[i, j] == background_color).all():
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
    
    # Get center of each cell
    
    # Aprox cell size 
    cell_size = (down_border[0] - top_border[0]) / 20
    offset = cell_size/2  # To get the aprox center of each cell

    # Create playing field of 20*10
    field_array = []
    for i in range(20):
        field_array.append([[], [], [], [], [],[], [], [], [], []])

    for i in range(20):
        for j in range(10):
            screen_i = int(top_border[0] + (i*cell_size) + offset)
            screen_j = int(left_border[1] + (j*cell_size) + offset)
            field_array[i][j] = Cell(screen_i, screen_j)
        
    # Get center of next pieces
    next_middle = next_left_border[1] + int((next_right_border[1] - next_left_border[1])/2)
    next_offset = int((next_down_border[0] - next_top_border[0])/3)
    next_locations = [[int(next_top_border[0]+next_offset*0.6), next_middle],
                      [int(next_top_border[0]+next_offset*1.6), next_middle],
                      [int(next_top_border[0]+next_offset*2.6), next_middle]]
                      
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
            
        for loc in next_locations:
            for i in range(next_middle-20, next_middle+20):
                img_array[loc[0], i] = [255, 255, 0, 255]
             
        for i in range(20):
            for j in range(10):
                for i2 in range(3):
                    for j2 in range(3):
                       img_array[field_array[i][j].screen_i+i2, field_array[i][j].screen_j+j2]  = [255, 0, 255, 255]
        
            
    return field_array, next_locations\
            
def get_next_pieces(img_array, next_locations):
    
    print()
    print("Next pieces are:")
    for loc in next_locations:
        # Hack: +1 to avoid looking at debug lines (always te same color)
        # print(str(loc[0])+"-"+str(loc[1])+": "+str(img_array[loc[0]+1, loc[1]+1]))
        
        if is_similar_color(img_array[loc[0]+1, loc[1]+1], T_color ): print("T piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], I_color ): print("I piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], z_color ): print("z piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], z2_color): print("z2 piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], L_color ): print("L piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], L2_color): print("L2 piece")
        elif is_similar_color(img_array[loc[0]+1, loc[1]+1], o_color): print("o piece")
        else: print("Unknown: "+str(img_array[loc[0]+1, loc[1]+1]))
        
def get_occupations(img_array, field_array, debug=False):

    for i in range(20):
        for j in range(10):
            x = field_array[i][j].screen_i - 5 # Hack: -5 to avoid debug area
            y = field_array[i][j].screen_j 
            if is_similar_color(img_array[x, y], background_color, 10):
                field_array[i][j].occupied = False
            else:
                field_array[i][j].occupied = True
        if debug:
        # for i in range(20):
            print([str(x.occupied).replace("True", "X").replace("False", " ") for x in field_array[i]])
                
if __name__=="__main__":
    while True:
        raw_img = screenshot.grab(bounding_box)
        img_array = np.array(raw_img)
        
        try:
            # Call this only at initialisation
            field_array, next_locations = detect_borders(img_array, debug=True)
            
            get_next_pieces(img_array, next_locations)
            
            get_occupations(img_array, field_array, debug=True)
        
        
        except Exception as e: print("Board not detected!")
                
        cv2.imshow('screen', img_array)    

        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            cv2.destroyAllWindows()
            break