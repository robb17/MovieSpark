import csv
from weights import init_weights

# Takes a list of pairs (movie_id, rating) and returns a list of triples with the movie name
def get_triples(movies):
    movie_reader = csv.reader(open('../../ml-20m/movies.csv', newline = ''), delimiter=',', quotechar = '"')
    next(movie_reader)
    movie_triples = []
    head = 0
    while (head < len(movies)):
        row = next(movie_reader)
        next_id = movies[head][0]
        while (int(row[0]) != next_id) :
            row = next(movie_reader)
        movie_triples.append([next_id, row[1], movies[head][1]])
        head += 1
    return movie_triples

# Takes a list of ratings and gets the highest rated 13779
# Returns a list of pairs (movie_id, rating)
def top_movies(movies):
    rated_movies = []
    for i in range(0, 131263):
        if (movies[i] >= 3.25):                   # Set to 3.25 because it splits at almost 13000
            rated_movies.append([i, movies[i]])
    return rated_movies

# Gets all rating from the ratings.csv file and gets average 0-5 rating for each movie
# Returns a list of these ratings
def get_ratings():
    movie_reader = csv.reader(open('../../ml-20m/ratings.csv', newline = ''), delimiter=',', quotechar = '"')
    ratings = [0] * 131263                   # There are 131263 total movies
    rating_count = [0] * 131263              # Parallel arrays to track total rating for a movie,
    count = 0                                # and number of ratings for that movie
    for row in movie_reader:
        if (row[0] == "userId"):             # Ignore header
            continue
        count += 1
        if ((count % 1000000) == 0) :        # To see progress
            print("ROW " + str(int(count / 1000000)) + " million")
        movie_id = int(row[1])
        rating_count[movie_id] += 1
        ratings[movie_id] += float(row[2])
    for i in range(0,131263):                # Get ratings 0-5
        if (rating_count[i] != 0) :
            ratings[i] = ratings[i] / rating_count[i]
    return ratings

# Returns a list of the top 13799 rated movies as triples (movie_id, movie_name, rating)
def get_movies():
    all_rated_movies = get_ratings()
    top_rated_movies = top_movies(all_rated_movies)
    top_movies_with_names = get_triples(top_rated_movies)
    return top_movies_with_names
    
top_movies = get_movies()
print(len(top_movies))
#ids = []
#for entry in top_13799_movies :
#    ids.append(entry[0])
#init_weights(ids)
