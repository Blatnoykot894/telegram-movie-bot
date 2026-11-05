import asyncio
import logging
import sys
import random as r
import os
from html import escape

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from commands import (
    list_bot_commands,
    START_COMMAND,
    SHOW_FILMES_COMMAND,
    ADD_FILMS_COMMAND,
    SEARCH_BY_ACTOR_COMMAND,
    FILTER_FILMS_COMMAND,
    SEARCH_BY_GENRE_COMMAND,
    DELETE_FILM_COMMAND,
    FAVOURITE_FILMS_COMMAND,
    ADD_FAVOURITE_FILM_COMMAND,
    DELETE_FAVOURITE_FILM_COMMAND,
    RANDOM_FILM_COMMAND
)
from data import read_data, write_data, delete_data, dict_read_data, dict_write_data, dict_delete_data

TOKEN = "8255066579:AAHAUUVElfaD5ZwlwFtbIhXA1-_Oejj14Ss"

dp = Dispatcher()


class FilmForm(StatesGroup):
    name = State()
    year = State()
    genre = State()
    rating = State()
    actor = State()
    description = State()
    poster = State()
    link = State()


class SearchForm(StatesGroup):
    actor_name = State()
    genre_name = State()


class FilterForm(StatesGroup):
    genre = State()
    year = State()


class DeleteForm(StatesGroup):
    delete = State()


rel_keyboard = ReplyKeyboardBuilder()
rel_keyboard.add(KeyboardButton(text="➕ Add another actor"))
rel_keyboard.add(KeyboardButton(text="✅ Continue"))
rel_keyboard.adjust(2)
actor_keyboard = rel_keyboard.as_markup(resize_keyboard=True)


def format_film(film: dict) -> str:
    name = escape(str(film.get("name", "Unknown Title")))
    year = escape(str(film.get("year", "")))
    genre = escape(str(film.get("genre", "Not specified")))
    rating = film.get("rating", 0.0)
    actors = film.get("actors", [])
    actors_str = ", ".join([escape(str(a)) for a in actors]) if actors else "No actors listed"
    description = escape(str(film.get("description", "No description available.")))
    link = film.get("link", "")

    title_line = f"<b>🎬 {name}</b>"
    if year:
        title_line += f" <b>({year})</b>"

    card = [
        title_line,
        f"🎭 <b>Genre:</b> {genre}",
        f"⭐ <b>Rating:</b> {rating}/10",
        f"👥 <b>Starring:</b> {actors_str}",
        f"📖 <i>{description}</i>"
    ]
    if link:
        card.append(f"🔗 <b>Link:</b> <a href='{escape(link)}'>More info</a>")
    return "\n".join(card)



PAGE_SIZE = 5


class FilmsPage(CallbackData, prefix="page"):
    page: int


class FilmOpen(CallbackData, prefix="film"):
    index: int
    page: int


class FilmFav(CallbackData, prefix="fav"):
    index: int
    page: int


def films_list_kb(films: list[dict], page: int):
    total_pages = max(1, (len(films) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE

    kb = InlineKeyboardBuilder()
    for i, film in enumerate(films[start:start + PAGE_SIZE], start=start):
        title = f"🎬 {film.get('name', '?')}"
        if film.get("year"):
            title += f" ({film['year']})"
        kb.button(text=title, callback_data=FilmOpen(index=i, page=page))
    kb.adjust(1)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=FilmsPage(page=page - 1).pack()))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=FilmsPage(page=page + 1).pack()))
    kb.row(*nav)

    return kb.as_markup(), page


def film_card_kb(index: int, page: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Add to favourite", callback_data=FilmFav(index=index, page=page))
    kb.button(text="⬅️ Back", callback_data=FilmsPage(page=page))
    kb.adjust(1)
    return kb.as_markup()


async def send_film_cards(message: Message, films: list[dict]) -> None:
    for film in films:
        card = format_film(film)
        poster = film.get("poster")
        if poster:
            try:
                await message.answer_photo(photo=poster, caption=card)
            except Exception:
                await message.answer(card)
        else:
            await message.answer(card)


@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("ℹ️ Nothing to cancel right now.")
        return
    await state.clear()
    await message.answer("❌ Action cancelled.", reply_markup=ReplyKeyboardRemove())


@dp.message(START_COMMAND)
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    greeting = (
        "👋 <b>Welcome to FilmLibrary Bot!</b>\n\n"
        "Your personal cinematic assistant. Use the menu or commands to explore, "
        "search, add, or manage your favorite movies effortlessly! 🍿🎬"
    )
    await message.answer(greeting)


@dp.message(FAVOURITE_FILMS_COMMAND)
async def show_favourite_films(message: Message):
    user_id = str(message.from_user.id)
    data = dict_read_data()
    user_movies = data.get(user_id, [])
    if not user_movies:
        await message.answer("You don't have favorite films yet.")
        return
    all_data = read_data()
    favs_movies = [film for film in all_data if film.get("name") in user_movies]
    if favs_movies:
        await message.answer("⭐ <b>Your Favorite Films:</b>")
        await send_film_cards(message, favs_movies)
    else:
        text = "Your favourite films:\n" + "\n".join([f"• {film}" for film in user_movies])
        await message.answer(text)


@dp.message(ADD_FAVOURITE_FILM_COMMAND)
async def add_favourite_film(message: Message):
    user_id = str(message.from_user.id)
    data = dict_read_data()
    fav_films = data.get(user_id, [])
    all_data = read_data()
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("Please write the correct name e.g. /addfav Harry Potter")
        return
    film_name = text_parts[1].strip()

    real_film_name = None
    for film in all_data:
        if film.get("name", "").lower() == film_name.lower():
            real_film_name = film.get("name")
            break

    if not real_film_name:
        await message.answer("Film is not found.")
        return
    if real_film_name in fav_films:
        await message.answer("This film already exists in your favorites.")
        return

    fav_films.append(real_film_name)
    data[user_id] = fav_films
    dict_write_data(data)
    await message.answer(f"Film '{real_film_name}' added to favorites!")

@dp.message(DELETE_FAVOURITE_FILM_COMMAND)
async def delete_favorite_film(message: Message):
    user_id = str(message.from_user.id)
    data = dict_read_data()
    fav_films = data.get(user_id, [])
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("Please write the correct name e.g. /delfav Harry Potter")
        return
    film_name = text_parts[1].strip()
    film_exists = False
    for film in fav_films:
        if film_name.lower() == film.lower():
            film_exists = True
            break
    if not film_exists:
        await message.answer("Film is not found in your favorites.")
        return
    dict_delete_data(user_id, film_name)
    await message.answer(f"Film '{film_name}' removed from favorites!")


@dp.message(RANDOM_FILM_COMMAND)
async def random_film(message: Message):
    all_data = read_data()
    if not all_data:
        await message.answer("No movies available in the database right now.")
        return
    random_f = r.choice(all_data)
    card = format_film(random_f)
    header = "🎬 <b>Random Movie Selection</b>\n\n" + card
    poster = random_f.get("poster")
    if poster:
        try:
            await message.answer_photo(photo=poster, caption=header)
        except Exception:
            await message.answer(header)
    else:
        await message.answer(header)



@dp.message(SHOW_FILMES_COMMAND)
async def show_handler(message: Message, state: FSMContext):
    await state.clear()
    films = read_data()
    if not films:
        await message.answer("📭 Your movie collection is currently empty. Add some movies to get started!")
        return
    markup, _ = films_list_kb(films, 0)
    await message.answer("🎥 <b>Your Movie Collection:</b>", reply_markup=markup)


@dp.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()


@dp.callback_query(FilmsPage.filter())
async def films_page_callback(callback: CallbackQuery, callback_data: FilmsPage):
    films = read_data()
    if not films:
        try:
            await callback.message.edit_text("📭 Your movie collection is empty.")
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer("📭 Your movie collection is empty.")
        await callback.answer()
        return

    markup, _ = films_list_kb(films, callback_data.page)
    text = "🎥 <b>Your Movie Collection:</b>"

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@dp.callback_query(FilmOpen.filter())
async def film_open_callback(callback: CallbackQuery, callback_data: FilmOpen):
    films = read_data()
    if callback_data.index >= len(films):
        await callback.answer("Film not found, try /show again.", show_alert=True)
        return

    film = films[callback_data.index]
    card = format_film(film)
    markup = film_card_kb(callback_data.index, callback_data.page)
    poster = film.get("poster")

    await callback.message.delete()
    if poster:
        try:
            await callback.message.answer_photo(photo=poster, caption=card, reply_markup=markup)
        except Exception:
            await callback.message.answer(card, reply_markup=markup)
    else:
        await callback.message.answer(card, reply_markup=markup)
    await callback.answer()


@dp.callback_query(FilmFav.filter())
async def film_fav_callback(callback: CallbackQuery, callback_data: FilmFav):
    films = read_data()
    if callback_data.index >= len(films):
        await callback.answer("Film not found.", show_alert=True)
        return

    film_name = films[callback_data.index].get("name")
    user_id = str(callback.from_user.id)
    data = dict_read_data()
    fav_films = data.get(user_id, [])

    if film_name in fav_films:
        await callback.answer("Already in favorites ⭐", show_alert=False)
        return

    fav_films.append(film_name)
    data[user_id] = fav_films
    dict_write_data(data)
    await callback.answer(f"'{film_name}' added to favorites!")



@dp.message(ADD_FILMS_COMMAND)
async def start_add_films(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎬 <b>Step 1/8:</b> Please enter the movie title (or type /cancel):")
    await state.set_state(FilmForm.name)


@dp.message(FilmForm.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📅 <b>Step 2/8:</b> Enter the release year (e.g., 2023):")
    await state.set_state(FilmForm.year)


@dp.message(FilmForm.year, F.text)
async def process_year(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (text.isdigit() and len(text) == 4):
        await message.answer("⚠️ Please enter a valid 4-digit year (e.g., 2010):")
        return
    await state.update_data(year=text)
    await message.answer("🎭 <b>Step 3/8:</b> Enter the movie genre (e.g., Sci-Fi, Drama):")
    await state.set_state(FilmForm.genre)


@dp.message(FilmForm.genre, F.text)
async def process_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text.strip())
    await message.answer("⭐ <b>Step 4/8:</b> Enter a rating from 0 to 10 (e.g., 8.5):")
    await state.set_state(FilmForm.rating)


@dp.message(FilmForm.rating, F.text)
async def process_rating(message: Message, state: FSMContext):
    try:
        rating = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Please enter a valid number (e.g., 7.5):")
        return
    if not 0 <= rating <= 10:
        await message.answer("⚠️ Rating must be between 0 and 10:")
        return
    await state.update_data(rating=rating)
    await message.answer("👥 <b>Step 5/8:</b> Enter the first actor's name:", reply_markup=actor_keyboard)
    await state.set_state(FilmForm.actor)


@dp.message(FilmForm.actor, F.text == "✅ Continue")
async def continue_actor(message: Message, state: FSMContext):
    await message.answer("📝 <b>Step 6/8:</b> Enter a short plot description:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.description)


@dp.message(FilmForm.actor, F.text == "➕ Add another actor")
async def another_actor(message: Message):
    await message.answer("👥 Enter the next actor's name:")


@dp.message(FilmForm.actor, F.text)
async def process_actor(message: Message, state: FSMContext):
    user_data = await state.get_data()
    current_actors = user_data.get("actors", [])
    current_actors.append(message.text.strip())
    await state.update_data(actors=current_actors)
    await message.answer("✨ Actor added successfully! Add another or click Continue:", reply_markup=actor_keyboard)


@dp.message(FilmForm.description, F.text)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("🖼️ <b>Step 7/8:</b> Please send the movie poster (image) or type 'none':", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.poster)


@dp.message(FilmForm.poster, F.photo)
async def process_poster_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(poster=photo_file_id)
    await message.answer("🔗 <b>Step 8/8:</b> Please send a website link for the movie (or type 'none'):")
    await state.set_state(FilmForm.link)


@dp.message(FilmForm.poster, F.text)
async def process_poster_text(message: Message, state: FSMContext):
    await state.update_data(poster="")
    await message.answer("🔗 <b>Step 8/8:</b> Please send a website link for the movie (or type 'none'):")
    await state.set_state(FilmForm.link)


@dp.message(FilmForm.link, F.text)
async def process_link(message: Message, state: FSMContext):
    link_text = message.text.strip()
    await state.update_data(link=link_text if link_text.lower() != "none" else "")
    user_data = await state.get_data()

    prepared_film = {
        "name": user_data.get("name"),
        "year": user_data.get("year"),
        "description": user_data.get("description"),
        "rating": user_data.get("rating", 0.0),
        "genre": user_data.get("genre"),
        "actors": user_data.get("actors", []),
        "poster": user_data.get("poster", ""),
        "link": user_data.get("link", ""),
    }
    all_films = read_data()
    all_films.append(prepared_film)
    write_data(all_films)

    await message.answer("🎉 <b>Success!</b> The movie has been saved to your collection.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@dp.message(SEARCH_BY_ACTOR_COMMAND)
async def cmd_search_by_actor(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔍 Enter an actor's name to search for movies:")
    await state.set_state(SearchForm.actor_name)


@dp.message(SearchForm.actor_name, F.text)
async def process_search_by_actor(message: Message, state: FSMContext):
    search_query = message.text.strip().lower()
    matched_films = []

    for film in read_data():
        film_actors = [str(actor).lower() for actor in film.get("actors", [])]
        if any(search_query in actor for actor in film_actors):
            matched_films.append(film)

    if matched_films:
        await message.answer(f"🔍 <b>Movies starring '{escape(message.text.strip())}':</b>")
        await send_film_cards(message, matched_films)
    else:
        await message.answer("❌ No movies found with this actor.")
    await state.clear()


@dp.message(SEARCH_BY_GENRE_COMMAND)
async def cmd_search_by_genre(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔍 Enter a genre to search:")
    await state.set_state(SearchForm.genre_name)


@dp.message(SearchForm.genre_name, F.text)
async def process_filter_by_genre(message: Message, state: FSMContext):
    search_query = message.text.strip().lower()
    matched_films = []

    for film in read_data():
        film_genre = str(film.get("genre", "")).lower()
        if search_query == film_genre:
            matched_films.append(film)

    if matched_films:
        await message.answer(f"🎯 <b>Movies in genre '{escape(message.text.strip())}':</b>")
        await send_film_cards(message, matched_films)
    else:
        await message.answer("❌ No movies found with this genre.")
    await state.clear()


@dp.message(FILTER_FILMS_COMMAND)
async def cmd_filter_films(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎯 Enter a film genre for filtering (e.g., Fantasy):")
    await state.set_state(FilterForm.genre)


@dp.message(DELETE_FILM_COMMAND)
async def cmd_search_by_name(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🗑️ Enter the exact title of the film you want to delete:")
    await state.set_state(DeleteForm.delete)


@dp.message(DeleteForm.delete)
async def delete_film(message: Message, state: FSMContext):
    search_query = message.text.strip().lower()
    matched_films = []

    for film in read_data():
        if search_query == str(film.get("name", "")).lower():
            matched_films.append(film)

    if matched_films:
        await message.answer("🗑️ <b>Found & Deleted Film:</b>")
        await send_film_cards(message, matched_films)
        await delete_data(search_query)
        await message.answer("✅ Film deleted successfully.")
        await state.clear()
    else:
        await message.answer("❌ No movie was found with that title.")
        await state.clear()


@dp.message(FilterForm.genre, F.text)
async def process_filter_genre(message: Message, state: FSMContext):
    await state.update_data(filter_genre=message.text.strip())
    await message.answer("📅 Enter a release year for filtering:")
    await state.set_state(FilterForm.year)


@dp.message(FilterForm.year, F.text)
async def process_filter_year(message: Message, state: FSMContext):
    user_data = await state.get_data()
    target_genre = user_data.get("filter_genre", "").lower()
    target_year = message.text.strip()

    matched_films = []
    for film in read_data():
        if (
            str(film.get("genre", "")).lower() == target_genre
            and str(film.get("year", "")) == target_year
        ):
            matched_films.append(film)

    if matched_films:
        await message.answer(f"🎯 <b>Filtering results ({target_genre.capitalize()}, {target_year}):</b>")
        await send_film_cards(message, matched_films)
    else:
        await message.answer("❌ No movies found matching these criteria.")
    await state.clear()


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(list_bot_commands)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

