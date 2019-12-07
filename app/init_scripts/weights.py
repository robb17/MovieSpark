import csv
#from . import db
#from .models import Movie, Tag


# Uses the csv files right now to get data
# init_weights() compares the tag relevances from genome-scores.csv for each pair of movies
# init_weights2() gets the top 50 tags for each movie and compares between movies
def init_weights():
    # Read in the tags and relevances for movies
    weight_reader = csv.reader(open('../ml-20m/genome-scores.csv', newline=''), delimiter=',', quotechar='|')
    next(weight_reader)
    movieList = []
    # Read in movie names (FOR DUBUGGING AND TESTING IF MOVIES ARE SIMILAR)
    movie_reader = csv.reader(open('../ml-20m/movies.csv', newline=''), delimiter=',', quotechar='|')
    next(movie_reader)
    movies = []
    for i in range(0,200):                          # Checking only 200 movies right now because of speed
        row = next(movie_reader)
        movies.append(row[1])                       # Movie names for checking if movies are similar
        movieList.append([])
        print("Getting data: " + str(i) + "...")    # To make sure we can see it running and that it isnt stuck
        for j in range(0,1128):                     # There are 1128 tags. Get all of them for this movie and put its relevance in a list
            row = next(weight_reader)
            val = float(row[2])
            movieList[i].append(val)
    
    weights = []                                    # A list that will contain triples (movie1, movie2, weight). In future will add to DB
    print()                                         # For clean output
    for i in range(0,200):                          # Again, just 200 movies tested
        print("Getting weights: " + str(i) + "...")
        for j in range(0,200):
            if (i == j): continue                   # Don't get the same movie on itself
            diff = 0
            k = 0
            for k in range(0,1128):
                diff += abs(float(movieList[i][k]) - float(movieList[j][k]))
            avg_diff = diff / 1128
            diff = 0
            for k in range(0,1128):
                if abs(float(movieList[i][k]) - float(movieList[j][k])) > avg_diff: # Only add diff if it's significant (greater than average diff from all tags)
                    diff += abs(float(movieList[i][k]) - float(movieList[j][k]))
            diff = int(diff / 1128 * 10000)         # Normalize to int 0-10000
            weights.append([i, j, diff])            # Add the triple to the list. HERE ADD TO DB
    
    
    # THE REST IS TO SEE IF ALGORITHM MATCHES MOVIES WELL
    for j in range(0,200):
        best_match = 0
        low_diff = 20000
        for i in range(199*j,199*j+199):
            curr = weights[i]
            if (curr[2] < low_diff):
                low_diff = curr[2]
                best_match = curr[1]
        print("The best movie match for " + str(movies[j]) + " is " + movies[best_match])
        

def init_weights2() :
    weight_reader = csv.reader(open('../ml-20m/genome-scores.csv', newline=''), delimiter=',', quotechar='|')
    next(weight_reader)
    tagList = []           # List of 50 tags for each movie
    movie_reader = csv.reader(open('../ml-20m/movies.csv', newline=''), delimiter=',', quotechar='|')
    next(movie_reader)
    movies = []

    for i in range(0,1000):                                         # 1000 movies here
        row = next(movie_reader)
        movies.append(row[1])
        print("Getting data: " + str(i))
        best_tags = []                                              # Parallel lists to keep track of 50 best tags
        best_tag_vals = []                                          # and their relevances for a movie
        for k in range(0,50):
            best_tags.append(0)
            best_tag_vals.append(0)
        for j in range(0,1128):
            row = next(weight_reader)
            val = float(row[2])                                     # Get the relevance of this tag
            to_replace = best_tag_vals.index(min(best_tag_vals))    # Least relevant tag (or 0) currently in the best_tags list
            if (val > best_tag_vals[to_replace]):                   # See if the current tag is relevant enough
                best_tag_vals[to_replace] = val
                best_tags[to_replace] = j
            
        tagList.append(best_tags)
            
    for i in range(0,1000):
        best_match = 0                                              # Highest number of shared tags from another movie
        match = -1
        for j in range(0,1000):
            if (i == j) :
                continue
            tag_compare = set(tagList[i] + tagList[j])              # Combine the top 50 tags lists and remove dups
            weight = 100 - len(tag_compare)                         # Length below 100 is number of shared tags
            if (weight > best_match):
                best_match = weight                                 # weight is what would go in the DB here
                match = j
        if (match == -1) :
            print("Failed to find match")
        else :
            print("The best movie match for " + movies[i] + " is " + movies[match] + " : " + str(match))

if __name__ == '__main__':
    init_weights()

