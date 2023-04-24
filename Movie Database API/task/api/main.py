from urllib import request

from flask import Flask, make_response, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
import sys



app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///name.db'
db = SQLAlchemy(app)

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    year = db.Column(db.String(20), nullable=False)
    genre = db.Column(db.String(80), nullable=False)
    actors = db.relationship("HumanInMovie", backref="movies")


class Human(db.Model):
    __tablename__ = "actors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=False)
    year_born = db.Column(db.String(20), nullable=False, unique=False)
    movies = db.relationship("HumanInMovie", backref="actors")


class HumanInMovie(db.Model):
    __tablename__ = "movie_actors"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(80), nullable=False, unique=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, unique=False)
    human_id = db.Column(db.Integer, db.ForeignKey("actors.id"), nullable=False, unique=False)


with app.app_context():
    db.drop_all()
    db.create_all()


class AddMovieToHuman(Resource):
    def post(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help="Id is not specified", required=False)
        parser.add_argument('name', type=str, help="Movie title is not specified", required=False)
        parser.add_argument('year', type=str, help="movie year is not specified", required=False)
        parser.add_argument('genre', type=str, help="Movie genre is not specified", required=False)
        parser.add_argument('roles', type=str, help="Movie roles are not specified", required=False)
        args = parser.parse_args()
        if not args["id"]:
            movie = Movie(
                name=args["name"],
                year=args["year"],
                genre=args["genre"]
            )
            db.session.add(movie)
            db.session.commit()
            movie_id = movie.id
        else:
            movie_id = Movie.query.filter_by(id=args["id"]).first().id
        role = args["roles"]
        human = Human.query.filter(id==Human.id).first()
        actor_to_add_role = HumanInMovie()
        actor_to_add_role.role = role
        actor_to_add_role.movie_id = movie_id
        actor_to_add_role.human_id = human.id
        db.session.add(actor_to_add_role)
        db.session.commit()


api.add_resource(AddMovieToHuman, '/humans/<int:id>/movies')


class AddHumanToMovie(Resource):

    def post(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help="Id is not specified", required=False)
        parser.add_argument("name", type=str, help="Actor name is not specified", required=False)
        parser.add_argument("year_born", type=str, help="Year of actor's birth is not specified", required=False)
        parser.add_argument("roles", type=str, help="Actor's role is not specified", required=True)
        args = parser.parse_args()
        if not args["id"]:
            actor = Human(
                name=args["name"],
                year_born=args["year_born"],
            )
            db.session.add(actor)
            db.session.commit()
            human_id = actor.id
        else:
            human_id = Human.query.filter_by(id=args["id"]).first().id
        movie = Movie.query.filter(id==Movie.id).first()
        role = args["roles"]
        actor_in_movie = HumanInMovie()
        actor_in_movie.role = role
        actor_in_movie.movie_id = movie.id
        actor_in_movie.human_id = human_id
        db.session.add(actor_in_movie)
        db.session.commit()


api.add_resource(AddHumanToMovie, '/movies/<int:id>/humans')


class MoviesView(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help="Movie title is not specified", required=True)
        parser.add_argument('year', type=str, help="movie year is not specified", required=True)
        parser.add_argument('genre', type=str, help="Movie genre is not specified", required=True)
        args = parser.parse_args()
        movie = Movie(name=args['name'], year=args['year'], genre=args['genre'])
        db.session.add(movie)
        db.session.commit()
        response = {"id": movie.id, "name": movie.name, "year": movie.year, "genre": movie.genre}
        return make_response(jsonify(response), 200)

    def get(self):
        genre = request.args.get('genre')
        if genre:
            movies = Movie.query.filter(Movie.genre == genre).all()
        else:
            movies = Movie.query.all()
        movies_response = {}
        movies_response["movies"] = [{"id": movie.id, "name": movie.name, "year": movie.year, "genre": movie.genre} for movie in movies]
        return make_response(jsonify(movies_response), 200)


api.add_resource(MoviesView, '/movies')


class MoviesByIdView(Resource):

    def get(self, id):
        movie = Movie.query.filter(id==Movie.id).first()
        actor_list = []
        for actor_id in movie.actors:
            actor = Human.query.filter(Human.id==actor_id.human_id).first()
            roles = actor_id.role
            actor_dict = {
                "name": actor.name,
                "role": roles
            }
            actor_list.append(actor_dict)
        movies_response = {}
        movies_response['movie'] = {
            "id": movie.id,
            "name": movie.name,
            "genre": movie.genre,
            "year": movie.year,
            "humans": actor_list
        }
        return make_response(jsonify(movies_response), 200)



api.add_resource(MoviesByIdView, '/movies/<int:id>')


class HumansView(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, help="Actor name is not specified", required=True)
        parser.add_argument("year_born", type=str, help="Year of actor's birth is not specified", required=True)
        args = parser.parse_args()
        actor = Human(name=args["name"], year_born=args["year_born"])
        db.session.add(actor)
        db.session.commit()
        humans_response = {"id": actor.id, "name": actor.name, "year_born": actor.year_born}
        return make_response(jsonify(humans_response), 200)

    def get(self):
        role = request.args.get('role')
        if role:
            actor_list = HumanInMovie.query.filter(HumanInMovie.role==role).all()
            actors = []
            for actor in actor_list:
                human = Human.query.filter(Human.id == actor.human_id).first()
                actors.append(human)
        else:
            actors = Human.query.all()
        humans_response = {}
        humans_response["humans"] = [{"id": actor.id, "name": actor.name} for actor in actors]
        return make_response(jsonify(humans_response), 200)


api.add_resource(HumansView, '/humans')


class HumansByIdView(Resource):

    def get(self, id):
        actor = Human.query.filter(Human.id == id).first()
        movies_list = []
        for movies_id in actor.movies:
            movie = Movie.query.filter(Movie.id == movies_id.movie_id).first()
            roles = movies_id.role
            movies_dict = {
                "name": movie.name,
                "role": roles
            }
            movies_list.append(movies_dict)
        actor_response = {}
        actor_response["human"] = {
            "id": actor.id,
            "name": actor.name,
            "year_born": int(actor.year_born),
            "movies": movies_list
        }
        return make_response(jsonify(actor_response), 200)


api.add_resource(HumansByIdView, "/humans/<int:id>")



@app.errorhandler(400)
def bad_request(e):
    print(e.data)
    return make_response(jsonify({"message": e.data['message']}), 400)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run(host='0.0.0.0', port=3333)
