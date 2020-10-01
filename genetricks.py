from tetricks import play_simulation
import random
import copy
import time
import tkinter as tk


class Gen:

    def __init__(self, holes_weight=None, placed_height_weight=None, max_height_weight=None, avg_height_weight=None,
                    height_diff_weight=None, non_tetris_line_weight=None, tetris_weight=None, move_weight=None):

        # Genes
        # if any is None, reroll all
        if None in [holes_weight, placed_height_weight, max_height_weight, avg_height_weight,
                    height_diff_weight, non_tetris_line_weight, tetris_weight, move_weight]:
                    
            self.holes_weight           = random.uniform(-100, 100)
            self.placed_height_weight   = random.uniform(-100, 100)
            self.max_height_weight      = random.uniform(-100, 100)
            self.avg_height_weight      = random.uniform(-100, 100)
            self.height_diff_weight     = random.uniform(-100, 100)
            self.non_tetris_line_weight = random.uniform(-100, 100)
            self.tetris_weight          = random.uniform(-100, 100)
            self.move_weight            = random.uniform(-100, 100)
                    
        else:
        
            self.holes_weight = holes_weight                      # 80    # Holes are very bad
            self.placed_height_weight = placed_height_weight      # 3     # Lowest placement of current tetro, redundant?
            self.max_height_weight = max_height_weight            # 0     # Lowest max height
            self.avg_height_weight = avg_height_weight            # 6     # Lower is better
            self.height_diff_weight = height_diff_weight          # 3     # Smooth surface is better
            self.non_tetris_line_weight = non_tetris_line_weight  # 40    # Lines are bad unless we need to clear holes
            self.tetris_weight = tetris_weight                    # 1000  # Tetris is goood
            self.move_weight = move_weight                        # 1 
        
        # Set after playing
        self.score  = None
        self.rounds = 0

    def mutate(self, mutation_rate, mutation_impact):
        
        if (random.random() < mutation_rate):
            self.holes_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.placed_height_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.max_height_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.avg_height_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.height_diff_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.non_tetris_line_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.tetris_weight += random.uniform(-mutation_impact, mutation_impact)
            
        if (random.random() < mutation_rate):
            self.move_weight += random.uniform(-mutation_impact, mutation_impact)
            
        return self

    def mate(self, other):
        return Gen(
                     random.choice([self.holes_weight,           other.holes_weight]),
                     random.choice([self.placed_height_weight,   other.placed_height_weight]),
                     random.choice([self.max_height_weight,      other.max_height_weight]),
                     random.choice([self.avg_height_weight,      other.avg_height_weight]),
                     random.choice([self.height_diff_weight,     other.height_diff_weight]),
                     random.choice([self.non_tetris_line_weight, other.non_tetris_line_weight]),
                     random.choice([self.tetris_weight,          other.tetris_weight]),
                     random.choice([self.move_weight,            other.move_weight])
                  )

    def play(self, max_rounds):
    
        self.score, self.rounds = play_simulation(max_rounds, 
                                                    self.holes_weight, 
                                                    self.placed_height_weight, 
                                                    self.max_height_weight, 
                                                    self.avg_height_weight,
                                                    self.height_diff_weight, 
                                                    self.non_tetris_line_weight, 
                                                    self.tetris_weight,
                                                    self.move_weight
                                                    )
        return self.score
        
    def __str__(self):
        return (    "Gen:\n"
                    "holes_weight           = "+str(self.holes_weight          )+"\n"\
                    "placed_height_weight   = "+str(self.placed_height_weight  )+"\n"\
                    "max_height_weight      = "+str(self.max_height_weight     )+"\n"\
                    "avg_height_weight      = "+str(self.avg_height_weight     )+"\n"\
                    "height_diff_weight     = "+str(self.height_diff_weight    )+"\n"\
                    "non_tetris_line_weight = "+str(self.non_tetris_line_weight)+"\n"\
                    "tetris_weight          = "+str(self.tetris_weight         )+"\n"\
                    "move_weight            = "+str(self.move_weight           )+"\n"\
                    "score                  = "+str(self.score                 )
                )
                
                
def select_random_weighted(ordered_population, selection_size):

    population = copy.deepcopy(ordered_population)  # deepcopy as we are going to pop from it
     
    score_sum = 0
    cumulative_score = []
    for gen in population:
        score_sum += gen.score
        cumulative_score.append(score_sum)
        
    selected_genes = []
    for i in range(selection_size):
    
        pick = random.uniform(0, score_sum)
        for i in range(len(cumulative_score)-1):
            if pick < cumulative_score[i]:
                selected_genes.append(population.pop(i)) # Remove from list to not take again
                cumulative_score.pop(i)                  # Remove from list to not take again
                break
                
    return selected_genes
        
       
def breed_new_generation(population, elite_size, breeders_side, random_size, mutation_rate, mutation_impact):
    
    # Sort by score
    population = sorted(population, key=lambda x: x.score, reverse = True)
    
    # Elite is carried directly
    new_population = population[:elite_size]

    # Mutate elite clone
    for p in population[:elite_size]:
        new_population.append(copy.deepcopy(p).mutate(mutation_rate, mutation_impact))
        
    # Add some random individuals
    new_population += [Gen() for _ in range(random_size)]
    
    # Select some breeders by random weighted
    breeders = select_random_weighted(population, breeders_side)
    
    # Mate them until filling the population
    while len(new_population) < population_size:
        child = random.choice(breeders).mate(random.choice(breeders))
        child.mutate(mutation_rate, mutation_impact)
        new_population.append(child)
    
    return new_population


def plot_evolution(gen_best_score, gen_avg_score, gen_worst_score, plot_name=""):

    root = tk.Tk()  
    # root = tk.Tk()  
    root.wm_title(plot_name)
    canvas = tk.Canvas(root,)
    canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
    max_x = 800
    max_y = 300
    x_margin = 100
    y_margin = 20
    root.geometry(str(max_x+x_margin)+"x"+str(max_y+y_margin))
    
    
    x_scale = max_x/len(gen_best_score)
    y_scale = (max_y-20)/ (gen_best_score[-1] * 1.2)
    
    # Draw axis
    # for x, r in enumerate(best_gen_routes):
    for x in range(len(gen_best_score)):
        try:
            if not x % int(100/x_scale):
                canvas.create_text(x*x_scale+x_margin, max_y+(y_margin/2), text=str(x))
        except:
            pass
    for y in range(max_y):
        try:
            if not y % 10:
                canvas.create_text(10,y, text="{:1.5f}".format((max_y-y)/y_scale))
                canvas.create_line(x_margin-8,y, x_margin-5, y, fill="black", width=1 )
        except:
            pass
            
    for x, g in enumerate(gen_best_score):
    
        # Mean of each gen
        y = gen_avg_score[x]
        canvas.create_line(x*x_scale+x_margin, max_y-(y*y_scale)+2,
                           x*x_scale+x_margin, max_y-(y*y_scale)-3,
                           fill="#aaddee", width=1) # light blue
        canvas.create_line((x*x_scale+x_margin)+2, max_y-(y*y_scale),
                           (x*x_scale+x_margin)-3, max_y-(y*y_scale),
                           fill="#aaddee", width=1) # light blue
        # # Worst of each gen
        y = gen_worst_score[x]
        canvas.create_line(x*x_scale+x_margin, max_y-(y*y_scale)+2,
                           x*x_scale+x_margin, max_y-(y*y_scale)-3,
                           fill="#bb3333", width=1) # red
        canvas.create_line((x*x_scale+x_margin)+2, max_y-(y*y_scale),
                           (x*x_scale+x_margin)-3, max_y-(y*y_scale),
                           fill="#bb3333", width=1) # red
        # Best of each gen
        y = gen_best_score[x]
        canvas.create_line(x*x_scale+x_margin, max_y-(y*y_scale)+2,
                           x*x_scale+x_margin, max_y-(y*y_scale)-3,
                           fill="#3333bb", width=1)   # blue
        canvas.create_line((x*x_scale+x_margin)+2, max_y-(y*y_scale),
                           (x*x_scale+x_margin)-3, max_y-(y*y_scale),
                           fill="#3333bb", width=1)   # blue
                           
    root.mainloop()

if __name__ == "__main__":

    # Manual calibration
    # holes_weight           = 80  
    # placed_height_weight   = 3   
    # max_height_weight      = 0   
    # avg_height_weight      = 6   
    # height_diff_weight     = 3   
    # non_tetris_line_weight = 40  
    # tetris_weight          = 1000
    # move_weight            = 1   

    # quick tests
    # max_generations = 10
    # max_rounds      = 10
    # games_per_round = 2
    # population_size = 10
    # elite_size      = 2
    # breeders_side   = 4
    # random_size     = 2
    # mutation_rate   = 0.05
    # mutation_impact = 10
    
    max_generations = 20
    max_rounds      = 1000
    games_per_round = 4
    population_size = 30
    elite_size      = 2
    breeders_side   = 10
    random_size     = 5
    mutation_rate   = 0.1
    mutation_impact = 10
    
    curated_gen = Gen(
                        holes_weight           = 80   ,
                        placed_height_weight   = 3    ,
                        max_height_weight      = 0    ,
                        avg_height_weight      = 6    ,
                        height_diff_weight     = 3    ,
                        non_tetris_line_weight = 40   ,
                        tetris_weight          = 1000 ,
                        move_weight            = 1   
                     )

    population = [Gen() for _ in range(population_size-1)]
    population.append(curated_gen)
    
    generation_best_score  = []
    generation_avg_score   = []
    generation_worst_score = []
    
    tic = time.time()
    total_tic = time.time()
    for generation in range(max_generations):
        print("\nGeneration "+str(generation))
        
        # Play some games with each gene and keep avg score
        for gen in population:
            score = 0
            for i in range(games_per_round):
                score += gen.play(max_rounds)
            gen.score = score/games_per_round

        # Print results
        population = sorted(population, key=lambda x: x.score, reverse = True)
        print([str(gen.score) for gen in population])
        print(population[0])
        print("toc: "+str(time.time() - tic))
        tic = time.time()

        # Keep generation statitics
        generation_best_score.append(max([x.score for x in population]))
        generation_avg_score.append(sum([x.score for x in population])/population_size)
        generation_worst_score.append(min([x.score for x in population]))
    
        # Create the next generation
        population = breed_new_generation(population, elite_size, breeders_side, random_size, mutation_rate, mutation_impact)
    
    print("Final population:")
    for gen in population:
        print(gen)
    
    print("total_toc: "+str(time.time() - total_tic))
    plot_evolution(generation_best_score, generation_avg_score, generation_worst_score)
    
    
    
    
    