
import copy

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


def is_similar_color(color1, color2, tolerance = 3):
    # colors are BGRA, only BGR are important
    is_similar = True
    for i in range(2):
        if not (color1[i] - tolerance < color2[i] < color1[i] + tolerance):
            is_similar = False
            break
    return is_similar
    

def print_occupations(occupations):
    # print to cmd
    for i in range(20):
        print([str(x).replace("True", "X").replace("False", " ") for x in occupations[i]])


class ScreenPosition:
    def __init__(self, screen_i, screen_j):
        self.screen_i = screen_i
        self.screen_j = screen_j
            

class Field:
    def __init__(self):
        # Create playing field of 20*10
        self.width  = 10
        self.height = 20
        
        # TODO: calibrate weight for heuristics
        self.placed_hight_weight = 1
        self.height_avg_weight   = 1
        self.holes_weight        = 5
        
        # All this to be returned
        self.left_border = None
        self.right_border = None
        self.top_border = None
        self.down_border = None
        self.next_left_border = None
        self.next_right_border = None
        self.next_top_border = None
        self.next_down_border = None
            
        # Create empty list for needed arrays
        self.screen_positions = []        
        for i in range(20):
            self.screen_positions.append([None, None, None, None, None, None, None, None, None, None])
            
        self.occupations = []  
        for i in range(20):
            self.occupations.append([None, None, None, None, None, None, None, None, None, None])
        
    def detect_playing_area(self, img_array):
            
        try:
            
            # Detect vertical borders
            for j in range(0, 800):
                i = 200
                if is_similar_color(img_array[i, j], background_color):
                    if not self.left_border:
                        self.left_border = [i, j]
                else:
                    if self.left_border and not self.right_border:
                        self.right_border = [i, j]
                                
            # Detect horizontal borders
            for i in range(0, 800):
                j = self.left_border[1] + 1
                if is_similar_color(img_array[i, j], background_color):
                    if not self.top_border:
                        self.top_border = [i, j]
                else:
                    if self.top_border and not self.down_border:
                        self.down_border = [i, j]
            
            # Get next piece vertical borders
            inside_border = False
            for j in range(self.right_border[1], 800):
                i = 200
                if is_similar_color(img_array[i, j], next_bounds_color):
                    if not inside_border:
                        inside_border = True
                        if self.next_left_border and not self.next_right_border:
                            self.next_right_border = [i, j]
                else:
                    if inside_border:
                        inside_border = False
                        if not self.next_left_border:
                            self.next_left_border = [i, j]
                        
            # Use vertical info for horizontal
            inside_border = False
            for i in range(0, 800):
                j = self.next_right_border[1]-5
                if is_similar_color(img_array[i, j], next_bounds_color):
                    if not inside_border:
                        inside_border = True
                        if self.next_top_border and not self.next_down_border:
                            self.next_down_border = [i, j]
                else:
                    if inside_border:
                        inside_border = False
                        if not self.next_top_border:
                            self.next_top_border = [i, j]
            
            # Aprox cell size 
            cell_size = (self.down_border[0] - self.top_border[0]) / 20
            x_offset = cell_size/2 + 5 # To get the aprox center of each cell
            y_offset = cell_size/2 - 5 # To get the aprox center of each cell

            # Assign a screen coordinate to each cell in screen_positions
            # The pixel in each coordinate is used to detect the state of each cell
            for i in range(20):
                for j in range(10):
                    screen_i = int(self.top_border[0] + (i*cell_size) + x_offset)
                    screen_j = int(self.left_border[1] + (j*cell_size) + y_offset)
                    self.screen_positions[i][j] = ScreenPosition(screen_i, screen_j)
                
            # Get screen coordinate of next pieces
            self.next_middle = self.next_left_border[1] + int((self.next_right_border[1] - self.next_left_border[1])/2)
            self.next_offset = int((self.next_down_border[0] - self.next_top_border[0])/3)
            self.next_locations = [[int(self.next_top_border[0]+self.next_offset*0.6), self.next_middle],
                              [int(self.next_top_border[0]+self.next_offset*1.6), self.next_middle],
                              [int(self.next_top_border[0]+self.next_offset*2.65), self.next_middle]]
                              
            # Return true if no errors
            return True
           
        except Exception as e:
            print("detect_playing_area FAILED")
            print(str(type(e))+" "+str(e))
            return False
                              
    def debug_playing_area(self, img_array):
        # For debugging only, careful as we are drawing on the original img
        
            # Draw playing field area
            for i in range(self.top_border[0], self.down_border[0]):
                img_array[i, self.left_border[1]]  = [0, 255, 0, 255]
                img_array[i, self.right_border[1]] = [0, 255, 0, 255]
            for j in range(self.left_border[1], self.right_border[1]):
                img_array[self.top_border[0], j]  = [0, 255, 0, 255]
                img_array[self.down_border[0], j] = [0, 255, 0, 255]
                          
            # Draw next piece area
            for i in range(self.next_top_border[0], self.next_down_border[0]):
                img_array[i, self.next_left_border[1]]  = [0, 255, 0, 255]
                img_array[i, self.next_right_border[1]] = [0, 255, 0, 255]
            for j in range(self.next_left_border[1], self.next_right_border[1]):
                img_array[self.next_top_border[0], j]  = [0, 255, 0, 255]
                img_array[self.next_down_border[0], j] = [0, 255, 0, 255]
                          
            # Draw detection axes
            for i in range(0, 800):
                j = self.left_border[1] + 1
                if self.top_border[0] < i < self.down_border[0]:
                    img_array[i, j] = [0, 255, 0, 255]
                else:
                    img_array[i, j] = [0, 0, 255, 255]
            for j in range(0, 800):
                i = 200
                if (self.left_border[1] < j < self.right_border[1]) or (self.next_left_border[1] < j < self.next_right_border[1]) :
                    img_array[i, j] = [0, 255, 0, 255]
                else:
                    img_array[i, j] = [0, 0, 255, 255]
                
            for i in range(0, 800):
                j = self.next_right_border[1]-5
                if self.next_top_border[0] < i < self.next_down_border[0]:
                    img_array[i, j] = [0, 255, 0, 255]
                else:
                    img_array[i, j] = [0, 0, 255, 255]
                    
            for i in range(self.next_top_border[0], self.next_down_border[0]):
                img_array[i, self.next_middle] = [255, 255, 0, 255]
                
            for loc in self.next_locations:
                for i in range(self.next_middle-20, self.next_middle+20):
                    img_array[loc[0], i] = [255, 255, 0, 255]
                 
            for i in range(20):
                for j in range(10):
                    for i2 in range(3):
                        for j2 in range(3):
                           img_array[self.screen_positions[i][j].screen_i+i2, self.screen_positions[i][j].screen_j+j2]  = [255, 0, 255, 255]
   
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
        # score = height_avg*(self.height_avg_weight) + higher*(self.placed_hight_weight) - holes*(self.holes_weight)
        return height_avg, higher, holes
            
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
                                raise StopIteration # Break of nested loop
                                
                # Save only if no collision
                last_valid_i = drop_i
                
        except StopIteration: pass
    
        # place dropped tetro in test board test_occupations
        self.place_tetromino(temp_tetromino, test_occupations, last_valid_i, drop_j)
        
        return test_occupations, last_valid_i
        
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
                
                test_occupations, placed_tetro_height = self.drop_test(tetromino, column)
                
                # TODO: in copied and modified field, not original one...
                height_avg, higher, holes = self.get_heuristics(test_occupations)
                
                score = height_avg*(self.height_avg_weight) + placed_tetro_height*(self.placed_hight_weight) - holes*(self.holes_weight)
                    
                # Keep movement with better heuristics
                if best_score is None or score > best_score:
                    # print("new best: "+str(heuristics)+", col "+str(column)+", rot "+str(rotation))
                    best_score         = score
                    best_column        = column
                    best_rotation      = rotation
                    best_occupations   = test_occupations
                    best_height_avg    = height_avg
                    best_placed_height = placed_tetro_height
                    best_holes         = holes
                    
            # rotate for next try
            tetromino.rotate_right()
            
        print("")
        print("best_score: "+str(best_score))
        print("holes_score:      "+str(best_holes         *(self.holes_weight)))
        print("height_sum_score: "+str(best_height_avg    *(self.height_avg_weight)))
        print("higher_score:     "+str(best_placed_height *(self.placed_hight_weight)))
            
        return best_column, best_rotation
