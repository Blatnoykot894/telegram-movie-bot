import json

def read_data(file_path="data.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_data(data, file_path="data.json"):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def delete_data(movie_name, file_path="data.json"):
    data = read_data(file_path)
    search_name = movie_name.strip().lower()
    updated_data = [item for item in data if str(item.get("name", "")).strip().lower() != search_name]
    write_data(updated_data, file_path)

def dict_read_data(file_path="favorites.json"):
    try:
        with open(file_path,"r",encoding="utf-8") as file:
            return json.load(file)
    except(FileNotFoundError,json.JSONDecodeError):
        return {}

def dict_delete_data(user_id,movie_name, file_path="favorites.json"):
    data = dict_read_data()
    if user_id not in data:
        return False
    search_name = movie_name.strip().lower()
    user_films = data[user_id]
    updated_films = [film for film in user_films if film.strip().lower() != search_name]
    if len(updated_films) == len(user_films):
        return False
    data[user_id] = updated_films
    dict_write_data(data)
    return True


def dict_write_data(data, file_path="favorites.json"):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    print(read_data())

      