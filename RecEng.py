import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD


class Recommender:

    def __init__(self, database):
        self.database = database

    def _build_matrix(self, build_type="groups", collection_name=""):
        """
        build_type = "groups"/"ratings"
        """

        users_arr = np.array([x["_id"] for x in self.database.get_all("User_Info")])
        users_dict = {x: i for i, x in enumerate(users_arr)}

        user_matr = []
        info_matr = []
        data_matr = []

        # Different matrix type

        # Group matrix
        if build_type == "groups":
            info_arr = []
            for x in self.database.get_all("User_Info"):
                for group in x['groups']:
                    info_arr.append(group)
                    user_matr.append(x['_id'])
                    info_matr.append(group)
                    data_matr.append(1)
            info_arr = np.unique(info_arr)

        # Ratings matrix
        elif build_type == "ratings":
            info_arr = []
            for x in self.database.get_all(collection_name):
                user = x["_id"]
                del x["_id"]
                for movie in x.keys():
                    info_arr.append(movie)
                    user_matr.append(user)
                    info_matr.append(movie)
                    data_matr.append(x[movie])
            info_arr = np.unique(info_arr)

        info_dict = {x: i for i, x in enumerate(info_arr)}

        user_matr = np.array([users_dict[x] for x in user_matr])
        info_matr = np.array([info_dict[x] for x in info_matr])
        matr = csr_matrix((data_matr, (user_matr, info_matr)), shape=(len(users_dict), len(info_dict)))
        return matr, users_dict, info_dict

    def _get_most_similar_vectors(self, matrix, row_index, num_of_vectors=5):
        """
        Get N most simular users
        """
        simularities = cosine_similarity(matrix[row_index], matrix)
        indexes = simularities.argsort()
        return indexes[0][-num_of_vectors-1:-1]

    def ratings_rec(self, user_id, return_num=10):
        if not self.database.get_one(user_id, "User_Info"):
            return []

        matrix, users, movies = self._build_matrix("ratings", "ratings")

        svd = TruncatedSVD(n_components=100)
        svd.fit(matrix)

        reverse_movies = {y: x for y, x in enumerate(movies)}

        y = svd.inverse_transform(svd.transform(matrix[users[user_id]].todense()))

        movies = []

        for key, value in sorted(enumerate(y[0]), key=lambda x: -x[1])[:return_num]:
            movies.append(self.database.get_one(int(reverse_movies[key]), "Movie_Info"))

        return movies

    def groups_rec(self, user_id, return_num=5):
        matrix, users, groups = self._build_matrix("groups", "User_Info")

        reverse_users = {y: x for y, x in enumerate(users)}

        movies = []

        for _id in reversed(self._get_most_similar_vectors(matrix, users[user_id], return_num)):
            for movie in self.database.get_one(int(reverse_users[_id]), "User_Info")['movies']:
                movies.append(self.database.get_one(movie, "Movie_Info"))

        return movies
