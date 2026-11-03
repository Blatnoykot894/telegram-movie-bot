from aiogram.filters import Command
from aiogram.types.bot_command import BotCommand

START_COMMAND = Command("start")
START_BOTCOMMAND = BotCommand(command="start", description="Start the conversation")

SHOW_FILMES_COMMAND = Command("showfilmes")
SHOWFILMES_BOTCOMMAND = BotCommand(command="showfilmes", description="Show all movies")

ADD_FILMS_COMMAND = Command("addfilms")
ADDFILMS_BOTCOMMAND = BotCommand(command="addfilms", description="Add a new movie")

SEARCH_BY_ACTOR_COMMAND = Command("search_by_actor")
SEARCH_BY_ACTOR_BOTCOMMAND = BotCommand(command="search_by_actor", description="Search movies by actor name")

FILTER_FILMS_COMMAND = Command("filter_films")
FILTER_FILMS_BOTCOMMAND = BotCommand(command="filter_films", description="Filter movies by genre and year")

SEARCH_BY_GENRE_COMMAND = Command("search_by_genre")
SEARCH_BY_GENRE_BOTCOMMAND = BotCommand(command="search_by_genre", description="Filter movies by genre")

DELETE_FILM_COMMAND = Command("delete_film")
DELETE_FILM_BOTCOMMAND = BotCommand(command="delete_film", description="Delete films")

FAVOURITE_FILMS_COMMAND = Command("fav")
FAVOURITE_FILMS_BOTCOMMAND = BotCommand(command="fav", description="Show Favourite Films")

ADD_FAVOURITE_FILM_COMMAND = Command("addfav")
ADD_FAVOURITE_FILM_BOTCOMMAND = BotCommand(command="addfav",description="Adding film to favourite films")

DELETE_FAVOURITE_FILM_COMMAND = Command("delfav")
DELETE_FAVOURITE_FILM_BOTCOMMAND = BotCommand(command="delfav",description="Deleting film from favourite films")

RANDOM_FILM_COMMAND = Command("random_film")
RANDOM_FILM_BOTCOMMAND = BotCommand(command="random_film",description="Giving to you a random film")


list_bot_commands = [
    START_BOTCOMMAND, 
    SHOWFILMES_BOTCOMMAND, 
    ADDFILMS_BOTCOMMAND, 
    SEARCH_BY_ACTOR_BOTCOMMAND, 
    FILTER_FILMS_BOTCOMMAND,
    SEARCH_BY_GENRE_BOTCOMMAND,
    DELETE_FILM_BOTCOMMAND,
    FAVOURITE_FILMS_BOTCOMMAND,
    ADD_FAVOURITE_FILM_BOTCOMMAND,
    DELETE_FAVOURITE_FILM_BOTCOMMAND,
    RANDOM_FILM_BOTCOMMAND
]


