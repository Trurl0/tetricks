
import copy
import win32api, win32gui
import time

# Color constants
background_color  = [73, 26, 12, 255]
background_color_2  = [68, 25, 12, 255]
background_color_3  = [60, 21, 10, 255]
background_color_4  = [52, 19,  9, 255]
next_bounds_color = [255, 255, 255, 255]
T_color  = [178, 100, 140, 255]
I_color  = [228, 225, 177, 255]
Z_color  = [182, 164, 239, 255]
S_color  = [171, 240, 177, 255]
L_color  = [129, 182, 239, 255]
J_color  = [228, 177, 148, 255]
O_color  = [187, 232, 251, 255]


def is_similar_color(color1, color2, tolerance = 3):
    # colors are BGRA, only BGR are important
    is_similar = True
    for i in range(2):
        if not (color1[i] - tolerance < color2[i] < color1[i] + tolerance):
            is_similar = False
            break
    return is_similar
    

def detect_tetromino(img_array, loc):
    letter = None
    if is_similar_color  (img_array[loc[0]+1, loc[1]+1], T_color, tolerance=10): letter = "T"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], I_color, tolerance=10): letter = "I"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], Z_color, tolerance=10): letter = "Z"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], S_color, tolerance=10): letter = "S"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], L_color, tolerance=10): letter = "L"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], J_color, tolerance=10): letter = "J"
    elif is_similar_color(img_array[loc[0]+1, loc[1]+1], O_color, tolerance=10): letter = "O"
    return letter
    
    
def print_occupations(occupations):
    # print to cmd
    for i in range(20):
        print([str(x).replace("True", "O").replace("False", " ") for x in occupations[i]])


def calculate_move(tetromino, column, rotation):

    # Initial position to calculate input needed to achieve final position
    initial_j = 3
    
    # Very hacky: get initial position based on type and rotations 
    if tetromino.letter == "O":
        initial_j = 4
    elif tetromino.letter == "I":
        if rotation == 1:
            initial_j = 5
        elif rotation == 3:
            initial_j = 4    # Leftwise rotation is different than three rights
    # L, J, S, Z and T are similar
    elif rotation == 1:
            initial_j = 4
            
    h_move = column - initial_j
    
    r_move = rotation
    if rotation == 3:
        r_move = -1
    
    return h_move, r_move


def check_cleared_lines(occupations, placed_tetromino, placed_tetro_height):
    # Check if the placed tetro clears some lines
    cleared_lines = []
    for i in range(placed_tetro_height, placed_tetro_height+placed_tetromino.height()):
        if all(occupations[i]):
            cleared_lines.append(i)
            
    # Remove cleared lines from occupations
    for i in cleared_lines:
    
        # Remove cleared line
        occupations.pop(i)   
        
        # Add empty one on top
        occupations.insert(0, [False, False, False, False, False, False, False, False, False, False])  
        
    return len(cleared_lines), occupations


def place_tetromino(tetromino, occupations, field_i, field_j):
    # occupy field with tetronimo in definitive position
    # Assumption: the tetro is in a verified final position
    for i, row in enumerate(tetromino.body):
        for j, occupied in enumerate(row):
            if occupied:
                occupations[i+field_i][j+field_j] = True
                  
             
def drop_tetromino(tetromino, drop_j, occupations):

    # Drop a copy of the tetromino on the field
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
                        if occupations[drop_i+i][drop_j+j]:
                            # print("Collision "+str(drop_i)+", "+str(drop_j))
                            raise StopIteration # Break of nested loop
                            
            # Save only if no collision
            last_valid_i = drop_i
            
    except StopIteration: pass

    # place dropped tetro in test board test_occupations
    place_tetromino(temp_tetromino, occupations, last_valid_i, drop_j)
    
    # Clean cleared lines
    cleared_lines, occupations = check_cleared_lines(occupations, temp_tetromino, last_valid_i)
    
    return occupations, temp_tetromino, last_valid_i, cleared_lines
           
           
def get_heights_and_holes(occupations):
    # Together to optimize search

    holes = 0
    column_heights     = []  # Height of each column (10 entries, one per column)
    column_height_diff = []  # Height diff between a column and the next (9 entries, between columns)
    
    # Iterate all columns
    for j in range(10):            
    
        first_occupation = False
        for i in range(20):
            if occupations[i][j]:
            
                # Store the height of this column
                if not first_occupation:
                    column_heights.append(20-i)
                first_occupation = True
                    
                if j>0:
                    column_height_diff.append(abs(column_heights[j] -  column_heights[j-1]))
                    
                    
            elif first_occupation:
                holes += 1
                
        # Empty column
        if not first_occupation:
            column_heights.append(0)
             
    return column_heights, column_height_diff, holes     


class ScreenPosition:
    def __init__(self, screen_i, screen_j):
        self.screen_i = screen_i
        self.screen_j = screen_j
            

class Field:
    def __init__(self, holes_weight, placed_height_weight, max_height_weight, avg_height_weight, height_diff_weight,\
                    non_tetris_line_weight, tetris_weight, move_weight):
        # Create playing field of 20*10
        self.width  = 10
        self.height = 20
        
        # Information to use in the next round
        self.holes = 0
        
        # Score weights for heuristics
        self.holes_weight           = holes_weight            # 80   # Holes are very bad
        self.placed_height_weight   = placed_height_weight    # 3     # Lowest placement of current tetro, redundant?
        self.max_height_weight      = max_height_weight       # 0     # Lowest max height
        self.avg_height_weight      = avg_height_weight       # 6     # Lower is better
        self.height_diff_weight     = height_diff_weight      # 3     # Smooth surface is better
        self.non_tetris_line_weight = non_tetris_line_weight  # 40    # Lines are bad unless we need to clear holes
        self.tetris_weight          = tetris_weight           # 1000  # Tetris is goood
        self.move_weight            = move_weight             # 1     # Less moves are better
        
        # Screen coordinates set at the start of the game
        self.up_left_corner    = None
        self.down_right_corner = None
        self.hold_pos          = None
        self.next_pos          = None
            
        # Create empty list for needed arrays
        self.screen_positions = []        
        for i in range(20):
            self.screen_positions.append([None, None, None, None, None, None, None, None, None, None])
            
        self.occupations = []  
        for i in range(20):
            self.occupations.append([False, False, False, False, False, False, False, False, False, False])
        
    def calibrate_manually(self, img_array):
        
        print()
        print("click upper left corner")
        while win32api.GetKeyState(0x01) >= 0: pass
        up_left_corner = win32gui.GetCursorPos()
        print(up_left_corner)
        time.sleep(0.3)
        
        print()
        print("click down right corner")
        while win32api.GetKeyState(0x01) >= 0: pass
        down_right_corner = win32gui.GetCursorPos()
        print(down_right_corner)
        time.sleep(0.3)
        
        print()
        print("click hold position")
        while win32api.GetKeyState(0x01) >= 0: pass
        hold_pos = win32gui.GetCursorPos()
        print(hold_pos)
        time.sleep(0.3)

        next_pos = []
        for i in range(3):
            print()
            print("click next position "+str(i+1))
            while win32api.GetKeyState(0x01) >= 0: pass
            next_pos.append(win32gui.GetCursorPos())
            print(next_pos)
            time.sleep(0.3)

        return up_left_corner, down_right_corner, hold_pos, next_pos
        
    def set_playing_area(self, up_left_corner, down_right_corner, hold_pos, next_pos):
        
        self.up_left_corner    = up_left_corner
        self.down_right_corner = down_right_corner
        self.hold_pos          = hold_pos
        self.next_pos          = next_pos
        
        # Careful, click coordinates are x, y, but img array are y, x
        
        # Aprox cell size 
        cell_size = (self.down_right_corner[1] - self.up_left_corner[1]) / 20
        x_offset = cell_size/2 + 5 # To get the aprox center of each cell
        y_offset = cell_size/2 - 5 # To get the aprox center of each cell
        # print(cell_size)

        # Assign a screen coordinate to each cell in screen_positions
        # The pixel in each coordinate is used to detect the state of each cell
        for i in range(20):
            for j in range(10):
                screen_i = int(self.up_left_corner[1] + (i*cell_size) + x_offset)
                screen_j = int(self.up_left_corner[0] + (j*cell_size) + y_offset)
                self.screen_positions[i][j] = ScreenPosition(screen_i, screen_j)
        
        return True
        
    def debug_playing_area(self, img_array):
    
        # Careful, click coordinates are x, y, but img array are y, x
        
        # Draw playing field area
        for i in range(self.up_left_corner[1], self.down_right_corner[1]):
            img_array[i, self.up_left_corner[0]]  = [0, 255, 0, 255]
            img_array[i, self.down_right_corner[0]] = [0, 255, 0, 255]
            
        for j in range(self.up_left_corner[0], self.down_right_corner[0]):
            img_array[self.up_left_corner[1], j]  = [0, 255, 0, 255]
            img_array[self.down_right_corner[1], j] = [0, 255, 0, 255]
                     
        # Draw cells
        for i in range(20):
            for j in range(10):
                for i2 in range(3):
                    for j2 in range(3):
                       img_array[self.screen_positions[i][j].screen_i+i2, self.screen_positions[i][j].screen_j+j2]  = [255, 0, 255, 255]
   
        # Draw next locations
        for pos in self.next_pos:
            for i in range(pos[1]-20, pos[1]+20):
                img_array[i, pos[0]] = [255, 255, 0, 255]
            for j in range(pos[0]-20, pos[0]+20):
                img_array[pos[1], j] = [255, 255, 0, 255]
             
        # Draw hold location
        for i in range(self.hold_pos[1]-20, self.hold_pos[1]+20):
            j = self.hold_pos[0]
            img_array[i, j] = [255, 255, 0, 255]
        for j in range(self.hold_pos[0]-20, self.hold_pos[0]+20):
            i = self.hold_pos[1]
            img_array[i, j] = [255, 255, 0, 255]

    def get_occupations_from_screen(self, img_array):
        
        for j in range(10):
            for i in range(20):
                x = self.screen_positions[i][j].screen_i
                y = self.screen_positions[i][j].screen_j 
                # print(str(i)+","+str(j)+": "+str(img_array[x, y]))
                
                # Hack, due to faded background, check against 3 references
                if is_similar_color(img_array[x, y], background_color, 5) or \
                   is_similar_color(img_array[x, y], background_color_2, 5) or \
                   is_similar_color(img_array[x, y], background_color_3, 5) or \
                   is_similar_color(img_array[x, y], background_color_4, 5):
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
        floating_occupations = []
        if empty_line:
            # print("Delete above line "+str(empty_line))
            for i in range(empty_line, -1, -1):
                # print("Delete line "+str(i))
                for j in range(10):
                    if self.occupations[i][j]:
                        floating_occupations.append((i, j))
                    self.occupations[i][j] = False
        return self.occupations, floating_occupations
            
    def get_next_tetrominos(self, img_array):
        
        # Careful, click coordinates are x, y, but img array are y, x
        next_tetrominos = []
        for loc in self.next_pos:
            # Hack: +1 to avoid looking at debug lines (always the same color)
            tetro_letter = detect_tetromino(img_array, loc[::-1])
            if tetro_letter is not None:
                next_tetrominos.append(tetro_letter)
            else:
                next_tetrominos.append("Unknown: "+str(img_array[loc[0]+1, loc[1]+1]))
            
        hold_tetromino = detect_tetromino(img_array, self.hold_pos[::-1])
        
        return next_tetrominos, hold_tetromino

    def get_heuristics(self, occupations, placed_tetromino, placed_tetro_height, cleared_lines, move_number):

        column_heights, column_height_diff, holes = get_heights_and_holes(occupations)
        
        max_height      = max(column_heights)
        avg_height      = sum(column_heights)/10
        new_holes       = holes - self.holes
        avg_height_diff = sum(column_height_diff)/10
        
        #-----------------------------------#
        # Score logic, this is the fun part #
        #-----------------------------------#
        score = 0
        
        # Decrease average height, quadratical impact
        score -= avg_height * avg_height * (self.avg_height_weight)
        
        # Choose lowest placement
        score -= (20-placed_tetro_height) * (self.placed_height_weight)
        
        # Choose lowest placement
        score -= max_height * max_height  * (self.max_height_weight)
        
        # Try not to make new holes
        score -= new_holes           * (self.holes_weight)
        
        # Try to make the surface as smooth as possible
        score -= avg_height_diff     * (self.height_diff_weight)
        
        # Less moves are better
        score -= move_number         * (self.move_weight)
                               
        # Tetris is very good
        if cleared_lines == 4:
            score += self.tetris_weight
            
        else:
            # If there are existing holes, clean them
            # Important not to check new holes, or we would try to generate holes to make line score positive!
            if self.holes:
                score += cleared_lines * self.non_tetris_line_weight
                
            # if not, avoid clearing lines
            else:
                score -= cleared_lines * self.non_tetris_line_weight
        #-----------------------------------#
        # Score logic, this is the fun part #
        #-----------------------------------#
        
        # return everyting for info purposes
        return score, max_height, avg_height, avg_height_diff, holes, new_holes, cleared_lines
        
    def calculate_best_drop(self,tetromino):
        # Assumptions:
        # we have space to move freely all the way
        
        best_column        = 0
        best_rotation      = 0
        
        best_h_move        = 0
        best_r_move        = 0
        
        best_score         = None
        best_height_sum    = None
        best_height_diff   = None
        best_higher        = None
        best_holes         = None
        best_occupations   = None
        best_cleared_lines = None
        
        
        # Test drop in every column and rotation
        for rotation in range(4):
            for column in range(self.width - tetromino.width() + 1):
                
                # Simulate placing a tetro in final position in a copy of the board
                test_occupations, temp_tetromino, placed_tetro_height, cleared_lines\
                = drop_tetromino(tetromino, column, copy.deepcopy(self.occupations))
                
                # Calculate input
                # This could be done only once with best move if we didn't want to use it for score
                h_move, r_move = calculate_move(temp_tetromino, column, rotation)
                
                # Number of key presses needed
                move_number = abs(h_move) + abs(r_move) 
                
                # Calculate score on the simulated field
                score, max_height, avg_height, avg_height_diff, holes, new_holes, cleared_lines\
                = self.get_heuristics(test_occupations, temp_tetromino, placed_tetro_height, cleared_lines, move_number)
                
                # Keep movement with better heuristics
                if best_score is None or score > best_score:
                    best_h_move        = h_move
                    best_r_move        = r_move
                    best_score         = score
                    best_column        = column
                    best_rotation      = rotation
                    best_occupations   = test_occupations
                    best_avg_height    = avg_height
                    best_max_height    = max_height
                    best_height_diff   = avg_height_diff
                    best_placed_height = placed_tetro_height
                    best_holes         = holes
                    best_new_holes     = new_holes
                    best_cleared_lines = cleared_lines
                    
            # rotate for next try
            tetromino.rotate_right()
            
                
        # Update future holes and occupations
        self.holes = best_holes
            
        return best_score         ,\
                best_h_move       ,\
                best_r_move       ,\
                best_occupations  ,\
                best_new_holes    ,\
                best_avg_height   ,\
                best_height_diff  ,\
                best_placed_height,\
                best_cleared_lines,\
                best_max_height   ,\
                best_column
