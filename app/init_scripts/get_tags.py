import csv

def get_all_tags():
	tag_reader = None
	try:
		tag_reader = csv.reader(open('../../../ml-20m/tags.csv', newline = ''), delimiter=',', quotechar = '"')
	except FileNotFoundError:
		tag_reader = csv.reader(open('../ml-20m/tags.csv', newline = ''), delimiter=',', quotechar = '"')
	next(tag_reader)
	movie_dict = {}
	for row in tag_reader:
		movie_id = int(row[1])
		if movie_dict.get(movie_id):
			movie_dict[movie_id].append(row[2])
		else:
			movie_dict[movie_id] = [row[2]]
	return movie_dict

def get_scored_tags():
	tag_reader = None
	try:
		tag_reader = csv.reader(open('../../../ml-20m/genome-tags.csv', newline = ''), delimiter=',', quotechar = '"')
	except FileNotFoundError:
		tag_reader = csv.reader(open('../ml-20m/genome-tags.csv', newline = ''), delimiter=',', quotechar = '"')
	next(tag_reader)
	tag_dict = {}
	count = 1
	for row in tag_reader:
		tag_dict[count] = row[1]
		count += 1
	return tag_dict

def get_tags_and_relevancy(movies):
	valid_movies_dictionary = {}
	for movie in movies:
		valid_movies_dictionary[movie[0]] = True
	relevancy_reader = None
	try:
		relevancy_reader = csv.reader(open('../../../ml-20m/genome-scores.csv', newline = ''), delimiter=',', quotechar = '"')
	except FileNotFoundError:
		relevancy_reader = csv.reader(open('../ml-20m/genome-scores.csv', newline = ''), delimiter=',', quotechar = '"')
	next(relevancy_reader)
	movie_dict = {}
	count = 0
	for row in relevancy_reader:
		movie_id = int(row[0])
		if valid_movies_dictionary.get(movie_id):
			if movie_dict.get(movie_id):
				movie_dict[movie_id].append(int(float(row[2]) * 10000))
			else:
				count += 1
				movie_dict[movie_id] = [int(float(row[2]) * 10000)]
	return movie_dict



if __name__ == '__main__':
	#movie_dict = get_tags_and_relevancy()
	#for x in range(0, 100):
	#	if movie_dict.get(x):
	#		print(movie_dict[x])
	tag_dict = get_scored_tags()
	for tag in tag_dict.keys():
		print(tag_dict[tag])

