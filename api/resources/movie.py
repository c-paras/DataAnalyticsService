from flask_restplus import abort, Resource, Namespace, reqparse

from movie_data import get_movie_data
from resources.genres_endpoint import get_genres
from resources.utils import release_date_and_year_strings_to_datetime
from .requires_auth import requires_auth

api = Namespace("movies", description="Movie data.")


def get_movie_or_404(movie_id):
    movie_data = get_movie_data()
    if movie_id in movie_data:
        return movie_data[movie_id]
    else:
        abort(404, "Movie not found.")


def get_movies_info(movie_ids):
    movie_data_dict = get_movie_data()
    movie_data_list = []
    for movie_id, movie_obj in movie_data_dict.items():
        if len(movie_ids) > 1 and not movie_id in movie_ids: continue
        if movie_obj["Title"] == '#DUPE#': continue
        new_movie_obj = movie_obj.copy()
        new_movie_obj['movie_id'] = movie_id
        movie_data_list.append(new_movie_obj)
    return movie_data_list


@api.param("movie_id", "Movie ID")
@api.route('/<string:movie_id>')
class Movie(Resource):
    @api.response(200, 'Movie found.')
    @api.response(404, 'Movie not found.')
    @api.doc(description="Get information about a particular movie.")
    @requires_auth(api)
    def get(self, movie_id):
        return get_movie_or_404(movie_id)




def sort_movies_by_title(movies):
    sorted_movies = list(sorted(movies, key=lambda x: x["Title"]))
    return sorted_movies


def sort_movies_by_release_date(movies, ascending=True):
    sorted_movies = list(sorted(
        movies,
        key=lambda x: release_date_and_year_strings_to_datetime(x["Released"], x["Year"]),
        reverse=(not ascending)
    ))
    return sorted_movies


def build_movielist_response(movies, limit=None):
    if limit is None:
        limit = len(movies)
    ret = movies[:limit]
    return {
        'movies': ret,
        'num_movies': len(ret)
    }


movie_list_req_parser = reqparse.RequestParser()
movie_list_req_parser.add_argument('limit', type=int, help="Limit number of results.", default=20)
movie_list_req_parser.add_argument('inTitle', type=str, help="Query movies by title.")

SORT_BY_RELEASE_DATE_ASC = "oldest"
SORT_BY_RELEASE_DATE_DESC = "newest"
SORT_BY_TITLE = "title"

movie_list_req_parser.add_argument('sortBy',
                                   choices=(SORT_BY_RELEASE_DATE_ASC, SORT_BY_RELEASE_DATE_DESC, SORT_BY_TITLE),
                                   help="Sort search results.",
                                   default=SORT_BY_TITLE)
movie_list_req_parser.add_argument('genre',choices=(),help="Query movies of a certain genre.")
@api.route('')
class MovieList(Resource):
    @api.response(200, 'Success.')
    @api.doc(description="Search for movies.")
    @api.expect(movie_list_req_parser)
    @requires_auth(api)
    def get(self):
        args = movie_list_req_parser.parse_args()
        limit = args.get('limit')
        inTitle = args.get("inTitle")
        if inTitle is None: inTitle = ""
        sortBy = args.get("sortBy")

        movie_data_list = get_movies_info([])
        filtered = [x for x in movie_data_list if inTitle in x["Title"].lower()]
        movie_data_list = filtered
        if sortBy == SORT_BY_TITLE:
            movie_data_list = sort_movies_by_title(movie_data_list)
        elif sortBy in [SORT_BY_RELEASE_DATE_DESC, SORT_BY_RELEASE_DATE_ASC]:
            order_ascending = sortBy == SORT_BY_RELEASE_DATE_ASC
            movie_data_list = sort_movies_by_release_date(movie_data_list, ascending=order_ascending)
        return build_movielist_response(movies=movie_data_list, limit=limit)
