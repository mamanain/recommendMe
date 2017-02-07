import urllib
import json
import vk
import time
import random
import os
import numpy as np


def _get_coded_string(string):
    value_utf8 = string.encode("utf-8")
    return urllib.parse.quote(value_utf8)


def get_movie_info(movie_name, api_key, desired_list=('id', 'title', 'original_title', 'genre_ids', 'poster_path')):
    URL = "https://api.themoviedb.org/3/search/movie?api_key={0}&language=ru&query={1}&page=1&include_adult=false"

    URL = URL.format(api_key, _get_coded_string(movie_name))

    response = urllib.request.urlopen(URL)

    response = response.read().decode("utf-8")

    js = json.loads(response)

    if len(js['results']) == 0:
        return []
    else:
        return {x: js['results'][0][x] for x in desired_list}


def get_data(_id, n, database, user_collection, api_key, min_num_of_movies=3):
    count = 0

    while database.get_collection_size(user_collection) < n:

        f = vk.get_friends(str(_id))

        friends = []
        for x in f:
            friends.append(str(x))

        friends_info = vk.get_users_info(friends)

        for friend in friends_info.keys():
            if database.get_collection_size(user_collection) >= n:
                break

            try:
                if count == 100:
                    time.sleep(1)
                    count = 0
                else:
                    count += 1
                if ("movies" in friends_info[friend].keys() and
                    len(friends_info[friend]["movies"].split(",")) >= min_num_of_movies and
                        len(friends) >= 5):

                    movies = []
                    min_len = 2
                    for movie in friends_info[friend]["movies"].split(","):
                        if len(movie) >= min_len:
                            m_info = get_movie_info(movie, api_key)
                            if len(m_info):

                                movies.append(m_info['id'])
                                m_info['_id'] = m_info['id']
                                del m_info['id']

                                # Inserting new movies

                                try:
                                    database.insert_one(m_info, "Movie_Info")
                                except Exception as e:
                                    continue

                    if len(movies) >= min_num_of_movies:

                        friends_info[friend]['_id'] = friends_info[friend]['uid']
                        del friends_info[friend]['uid']
                        friends_info[friend]['movies'] = movies

                        try:
                            # Inserting new user, plus his rating

                            f = friends_info[friend]
                            f['groups'] = vk.get_groups(f['_id'])['groups']['items']
                            f = {x: f[x] for x in ["movies", "groups", "_id"]}

                            rating = {str(x): 10 for x in f['movies']}
                            rating["_id"] = f["_id"]

                            database.insert_one(f, "User_Info")
                            database.insert_one(rating, "ratings")

                        except Exception as e:
                            continue
            except:
                pass

        if database.get_collection_size(user_collection) < n:
            last_id = _id
            while True:
                ind = random.randint(0, len(friends) - 1)
                if (len(vk.get_friends(friends[ind])) >= 5 and
                        last_id != friends[ind]):
                    _id = friends[ind]
                    break


def download_avatars(database):
    ids = list(map(lambda x: x['_id'], database.get_all("User_Info")))
    info = vk.get_users_info(ids, ['photo_100'])
    downloaded = np.array(list(map(lambda x: x.split(".")[0], os.listdir("Images/"))))

    new = [x for x in info.values() if x not in downloaded]

    for user in new:
        urllib.request.urlretrieve(user['photo_100'], 'Images/{0}.png'.format(user['uid']))