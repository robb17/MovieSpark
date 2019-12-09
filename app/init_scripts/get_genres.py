def get_genres(movies):
    genres = []
    for movie in movies:
        for genre in movie[3]:
            if genre not in genres:
                genres.append(genre)
    return genres