import requests
from hstest import FlaskTest, wrong, correct, dynamic_test


class MovieDatabaseAPIError(Exception):
    def __init__(self, error_resp):
        self.msg = error_resp["error"]

    def __str__(self):
        return f"{self.msg}"


class Test(FlaskTest):
    source = "api.main"
    use_database = True

    @property
    def movies_url(self):
        return self.get_url("/movies")

    @property
    def humans_url(self):
        return self.get_url("/humans")

    @property
    def example_movies(self):
        return [
            {"name": "Biba",
             "year": "1999",
             "genre": "comedy"},
            {"name": "Boba",
             "year": "2099",
             "genre": "horror"}
        ]

    @property
    def example_humans(self):
        return [
            {"name": "Pupa",
             "year_born": 2012},
            {"name": "Graham Chapman",
             "year_born": 1941}
        ]

    @dynamic_test
    def check_stage_one_endpoints(self):
        try:
            example_movies = self.example_movies.copy()
            for example_movie in example_movies:
                create_movie_resp = requests.post(self.movies_url, json=example_movie)
                if create_movie_resp.status_code != 200:
                    raise MovieDatabaseAPIError(create_movie_resp.json())

                movie_id = create_movie_resp.json().get("id")
                if not movie_id:
                    return wrong("Expected to get movie id in the creation response!")
                example_movie["id"] = movie_id

                get_movie_details_resp = requests.get(f"{self.movies_url}/{movie_id}")
                if get_movie_details_resp.status_code != 200:
                    raise MovieDatabaseAPIError(get_movie_details_resp.json())

                movie_info = get_movie_details_resp.json().get("movie")
                if not movie_info:
                    return wrong("Detailed movie endpoint should return movie info in json accessible by 'movie' key!")

                for key, value in example_movie.items():
                    if movie_info.get(key) != value:
                        return wrong(
                            f"Detailed movie endpoint seems to return incorrect value for the {key} field.")

            get_movies_resp = requests.get(self.movies_url)
            if get_movies_resp.status_code != 200:
                raise MovieDatabaseAPIError(get_movies_resp.json())

            movies_list = get_movies_resp.json().get("movies")
            if not movies_list:
                return wrong("Movie list endpoint should return list movies in json accessible by 'movies' key!")
            for example_movie in example_movies:
                if not any([returned_movie["id"] == example_movie["id"] for returned_movie in movies_list]):
                    return wrong("Movies list endpoint seems to not return all movies with ids.")
                if not any([returned_movie["name"] == example_movie["name"] for returned_movie in movies_list]):
                    return wrong("Movies list endpoint seems to not return all movies with names.")
                if not any([returned_movie["genre"] == example_movie["genre"] for returned_movie in movies_list]):
                    return wrong("Movies list endpoint seems to not return all movies with genres.")

            return correct()
        except MovieDatabaseAPIError as e:
            return wrong(str(e))
        except Exception as e:
            return wrong(f"Caught unexpected error: {str(e)}")

    @dynamic_test
    def check_stage_two_endpoints(self):
        try:
            example_humans = self.example_humans.copy()
            for example_human in example_humans:
                create_human_resp = requests.post(self.humans_url, json=example_human)
                if create_human_resp.status_code != 200:
                    raise MovieDatabaseAPIError(create_human_resp.json())

                human_id = create_human_resp.json().get("id")
                if not human_id:
                    return wrong("Expected to get human id in the creation response!")
                example_human["id"] = human_id

                get_human_details_resp = requests.get(f"{self.humans_url}/{human_id}")
                if get_human_details_resp.status_code != 200:
                    raise MovieDatabaseAPIError(get_human_details_resp.json())

                human_info = get_human_details_resp.json().get("human")
                if not human_info:
                    return wrong("Detailed human endpoint should return human info in json accessible by 'human' key!")

                for key, value in example_human.items():
                    if human_info.get(key) != value:
                        return wrong(
                            f"Detailed human endpoint seems to return incorrect value for the {key} field.")

            get_humans_resp = requests.get(self.humans_url)
            if get_humans_resp.status_code != 200:
                raise MovieDatabaseAPIError(get_humans_resp.json())

            humans_list = get_humans_resp.json().get("humans")
            if not humans_list:
                return wrong("Perons list endpoint should return list of humans in json accessible by 'humans' key!")
            for example_human in example_humans:
                if not any([returned_human["id"] == example_human["id"] for returned_human in humans_list]):
                    return wrong("humans list endpoint seems to not return all humans with ids.")
                if not any([returned_human["name"] == example_human["name"] for returned_human in humans_list]):
                    return wrong("humans list endpoint seems to not return all humans with names.")

            return correct()
        except MovieDatabaseAPIError as e:
            return wrong(str(e))
        except Exception as e:
            return wrong(f"Caught unexpected error: {str(e)}")

    @dynamic_test
    def check_stage_three_endpoints(self):
        try:
            # test connecting people to a movie
            movie_id = 1
            movie_resp = requests.get(f"{self.movies_url}/{movie_id}")
            movie = movie_resp.json().get("movie")
            self._get_response_field_or_throw(movie, "humans", "movie")
            # test adding new human to a movie
            self._add_and_check_human(movie_id, {"name": "Unique human to test",
                                                 "year_born": 1984,
                                                 "roles": ["actor"]})
            # test adding existing human to a movie
            self._add_and_check_human(movie_id, {"id": 1,
                                                 "roles": ["director"]})

            # test connecting movies to a human
            human_id = 2
            human_resp = requests.get(f"{self.humans_url}/{human_id}")
            human = human_resp.json().get("human")
            self._get_response_field_or_throw(human, "movies", "human")
            # test adding new movie to a human
            self._add_and_check_movie(human_id, {"name": "Unique movie to test",
                                                 "year": 1969,
                                                 "genre": "drama",
                                                 "roles": ["actor"]})
            # test adding existing movie to a human
            self._add_and_check_movie(movie_id, {"id": 1,
                                                 "roles": ["director"]})
            return correct()

        except MovieDatabaseAPIError as e:
            return wrong(str(e))
        except Exception as e:
            return wrong(f"Caught unexpected error: {str(e)}")

    @dynamic_test
    def check_stage_four_endpoints(self):
        try:
            # check movies filtering
            get_all_movies_resp = requests.get(self.movies_url)
            if get_all_movies_resp.status_code != 200:
                raise MovieDatabaseAPIError(get_all_movies_resp.json())

            all_movies_list = get_all_movies_resp.json().get("movies")

            comedy_movies_count = sum([1 if movie["genre"] == "comedy" else 0
                                       for movie in all_movies_list])
            comedy_movies_resp = requests.get(f"{self.movies_url}?genre=comedy")
            if comedy_movies_resp.status_code != 200:
                raise MovieDatabaseAPIError(comedy_movies_resp.json())

            comedy_movies_list = comedy_movies_resp.json().get("movies")
            if len(comedy_movies_list) != comedy_movies_count:
                raise MovieDatabaseAPIError("Filtered movies request returned unexpected number of movies.")

            # check humans filtering
            get_all_humans_resp = requests.get(self.humans_url)
            if get_all_humans_resp.status_code != 200:
                raise MovieDatabaseAPIError(get_all_humans_resp.json())

            for i in range(3):
                creation_resp = requests.post(f"{self.movies_url}/1/humans",
                                              json={"name": f"Testhuman{i}",
                                                    "year_born": 2012,
                                                    "roles": ["special_role"]})
                if creation_resp.status_code != 200:
                    raise MovieDatabaseAPIError(creation_resp.json())

            special_humans_resp = requests.get(f"{self.humans_url}?role=special_role")
            if special_humans_resp.status_code != 200:
                raise MovieDatabaseAPIError(special_humans_resp.json())

            special_humans_list = special_humans_resp.json().get("humans")
            if len(special_humans_list) != 3:
                raise MovieDatabaseAPIError("Filtered humans request returned unexpected number of humans.")

            return correct()

        except MovieDatabaseAPIError as e:
            return wrong(str(e))
        except Exception as e:
            return wrong(f"Caught unexpected error: {str(e)}")

    def _get_response_field_or_throw(self, resp: dict, field: str, resp_type: str):
        field_data = resp.get(field)
        if field_data is None:
            raise MovieDatabaseAPIError(f"Response for {resp_type} should contain field {field}")
        return field_data

    def _add_and_check_human(self, movie_id, human_info):
        creation_resp = requests.post(f"{self.movies_url}/{movie_id}/humans",
                                      json=human_info)
        if creation_resp.status_code != 200:
            raise MovieDatabaseAPIError(creation_resp.json())

        movie_resp = requests.get(f"{self.movies_url}/{movie_id}")
        movie_humans = self._get_response_field_or_throw(movie_resp.json().get("movie"),
                                                         "humans", "movie")
        for human in movie_humans:
            id_provided = human_info.get("id")
            if id_provided:
                p = requests.get(f"{self.humans_url}/{id_provided}").json()
                if p["human"]["name"] == human["name"]:
                    return
            else:
                if human["name"] == human_info["name"] and \
                        human["role"] in human_info["roles"]:
                    if len(human_info["roles"]) > 1:
                        human_info["roles"].remove(human["role"])
                        continue
                    else:
                        return

        raise MovieDatabaseAPIError("""human added to a movie was not found in 
        movie details response or some of the fields is missing""")

    def _add_and_check_movie(self, human_id, movie_info):
        creation_resp = requests.post(f"{self.humans_url}/{human_id}/movies",
                                      json=movie_info)
        if creation_resp.status_code != 200:
            raise MovieDatabaseAPIError(creation_resp.json())

        human_resp = requests.get(f"{self.humans_url}/{human_id}")
        human_movies = self._get_response_field_or_throw(human_resp.json().get("human"),
                                                         "movies", "human")
        for movie in human_movies:
            id_provided = movie_info.get("id")
            if id_provided:
                m = requests.get(f"{self.movies_url}/{id_provided}").json()
                if m["movie"]["name"] == movie["name"]:
                    return
            else:
                if movie["name"] == movie_info["name"] and \
                        movie["role"] in movie_info["roles"]:
                    if len(movie_info["roles"]) > 1:
                        movie_info["roles"].remove(movie["role"])
                        continue
                    else:
                        return

        raise MovieDatabaseAPIError("""human added to a movie was not found in 
         movie details response or some of the fields is missing""")


if __name__ == '__main__':
    Test().run_tests()
