import csv
#from weights import init_weights

MAX_MOVIES = 12000
BIAS_THRESHOLD = 50

# Takes a list of pairs (movie_id, rating) and returns a list of triples with the movie name
def combine_attributes(movies):
    movie_reader = csv.reader(open('../ml-20m/movies.csv', newline = ''), delimiter=',', quotechar = '"')
    next(movie_reader)
    movie_triples = []
    movie_set = {}
    for row in movie_reader:    # movie id, movie title, movie year
        title, year = parse_title(row[1])
        movie_set[int(row[0])] = [title, year, row[2]]
    for rated_movie in movies:
        if movie_set.get(rated_movie[0]):
            new_attributes = movie_set[rated_movie[0]]
            genres = new_attributes[2].split("|")
            movie_triples.append([rated_movie[0], new_attributes[0], new_attributes[1], [genres[x] for x in range(0, len(genres))], rated_movie[1]])
    return movie_triples

# Takes a list of id, rating, and weighted rating
# Sorts by weighted rating and trims to top 10000
def top_movies(movies):
    movies.sort(key=lambda x: x[2], reverse=True)
    return movies[:MAX_MOVIES]

def parse_title(unparsed_title):
    title = None
    year = None
    for x in range(len(unparsed_title) - 1, 0, -1):
        if unparsed_title[x] == "(":
            try:
                year = int(unparsed_title[x + 1:-1].replace(")", ""))
            except ValueError:
                pass    # some movies dont specify year in this dataset
            title = unparsed_title[:x - 1]
            break
    return (title, year)


def n_movies(reader):
    max_id = 0
    for row in reader:
        movie_id = None
        try:
            movie_id = int(row[1])
        except ValueError:
            pass
        if movie_id:
            max_id = movie_id if movie_id > max_id else max_id
    return max_id + 1

# Gets all rating from the ratings.csv file and gets average 0-5 rating for each movie
# Returns a list of sublists containing id, rating, and weighted rating
# Weighted rating needed so that obscure movies with few reviews aren't heavily selected for
def get_ratings():
    with open('../ml-20m/ratings.csv', newline = '') as f:
        movie_reader = csv.reader(f, delimiter=',', quotechar = '"')
        n_m = n_movies(movie_reader)
        f.seek(0)
        ratings = [0] * n_m
        rating_count = [0] * n_m
        weighted_rating = [0] * n_m
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
        for i in range(0, len(ratings)):                # Get ratings 0-5
            if (rating_count[i] != 0) :
                ratings[i] = ratings[i] / rating_count[i]
        for i in range(0, len(ratings)):
            weighted_rating[i] = ratings[i] if rating_count[i] > BIAS_THRESHOLD else ratings[i] * (((rating_count[i] / 2) + (BIAS_THRESHOLD / 2)) / BIAS_THRESHOLD)
        movies = [[x, ratings[x], weighted_rating[x]] for x in range(1, len(ratings))]
        return movies

# Returns a list of the top 10000 rated movies as (movie_id, movie_name, year, (genre1, genre2, ...), rating)
def get_movies():
    all_rated_movies = get_ratings()
    top_rated_movies = top_movies(all_rated_movies)
    top_movies_with_names = combine_attributes(top_rated_movies)
    return top_movies_with_names
    
if __name__ == '__main__':
    top_movies = get_movies()
    print(len(top_movies))
    for i in range(MAX_MOVIES - 1000, MAX_MOVIES):
        print(top_movies[i])
#ids = []
#for entry in top_13799_movies :
#    ids.append(entry[0])
#init_weights(ids)
