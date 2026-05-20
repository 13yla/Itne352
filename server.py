import socket # to create a tcp server that listen for incoming connections from clients and handle their requests
import threading # to handle each client in a separate thread to handle  at  least 3 clients
import json # to save the cache and recipe responses to files in json format 
import requests # pyright: ignore[reportMissingModuleSource] # to make http requests to the mealdb api to get the data we need for our server

# server setting 
HOST = '127.0.0.1'  # local machine address 
PORT = 5000        # door number for connection 
GROUP_ID = "B4"     
BASE_URL = "https://www.themealdb.com/api/json/v1/1"

# this  stores the fixed data in momery 
referance_cache ={
"categories":[], 
"areas":[],
"ingredients":[],
}

# this function runs once when server start 
def load_reference_cache():
    #get all categories 
    response = requests.get(f"{BASE_URL}/list.php?c=list")
    referance_cache["categories"]= response.json().get("meals", [])# use get to avoid error if the key is not exist and return empty list instead of None
    print(f"categories loaded:{len(referance_cache['categories'])}")

    #get all areas 
    response = requests.get(f"{BASE_URL}/list.php?a=list")
    referance_cache["areas"]= response.json().get("meals", [])
    print(f"areas loaded:{len(referance_cache['areas'])}")

    #get all ingredients 
    response = requests.get(f"{BASE_URL}/list.php?i=list")
    referance_cache["ingredients"]= response.json().get("meals", [])
    print(f"ingredients loaded:{len(referance_cache['ingredients'])}")

    # save cache to file 
    file_data ={
        "categories": referance_cache ["categories"],
        "areas": referance_cache ["areas"],
        "ingredients": referance_cache ["ingredients"][:50]
    }

    with open(f"reference_{GROUP_ID}.json", "w") as f:
        json.dump(file_data, f,indent=2)

# save each  recipe response to file 
def save_recipe_file(client_name ,option , data):
    filename = f"{client_name}_{option}-{GROUP_ID}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

# send data to client
def send_data(conn, data):
    message = (json.dumps(data, ensure_ascii=False) + "\n").encode('utf-8') # use dumps to trensfreind data to json format when we send it to client and ensure_ascii=False to support non-english characters
    conn.sendall(message) # use sendall to ensure that all data is sent to client in tcp connection

# recive data from client
def receive_data(conn):
    buffer = "" # use buffer to store the incoming data until we receive the full message
    while True:
        chunk = conn.recv(4096).decode('utf-8')
        if not chunk: # if the client disconnected or there is an error in receiving data
            return None
        buffer += chunk
        if "\n" in buffer: # use \n as a delimiter to indicate the end of the length data
            break
    message_str = buffer.split("\n")[0] # use split to get the length data from the buffer
    try:
        return json.loads(message_str) # use loads to convert the json string back to a python dictionary
    except json.JSONDecodeError:
        return None

#get full details of meal
def get_full_details(meal):

    #get ingredients with their measures
    ingredients = []
    for i in range(1, 21):
        ingredient = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ingredient and ingredient.strip(): # use strip to remove any extra spaces and check if the ingredient is not empty after stripping
            ingredients.append(f"{measure.strip()} {ingredient.strip()}") #use append to add in the end of the list 
    # return the full details of the meal in a structured format
    return {
        "strMeal": meal.get("strMeal", ""),
        "strCategory": meal.get("strCategory", ""), #  ""  use  to avoid error if the key is not exist and return empty string instead of None
        "strArea": meal.get("strArea", ""),
        "strInstructions": meal.get("strInstructions", ""),
        "ingredients": ingredients,
        "strYoutube": meal.get("strYoutube", ""),
        "strSource": meal.get("strSource", ""),
        "strTags": meal.get("strTags", "")
    }

#search for meal by name
def search_by_name(keyword):
    response = requests.get(f"{BASE_URL}/search.php?s={keyword}")
    meals = response.json().get("meals") or []
    result = []
    for meal in meals[:15]:
        result.append({
            "idMeal": meal["idMeal"],
            "strMeal": meal["strMeal"], 
            "strMealThumb": meal["strMealThumb"]
        })
    return result

#filter meals by category
def filter_by_category(category):
    response = requests.get(f"{BASE_URL}/filter.php?c={category}")
    meals = response.json().get("meals") or []
    result = [] #empty list to store the filtered meals                                                                                              
    for meal in meals[:15]: # show only the first 15 meals 
        result.append({
            "idMeal": meal["idMeal"],
            "strMeal": meal["strMeal"],
            "strMealThumb": meal["strMealThumb"]
        })
    return result

#filter meals by area
def filter_by_area(area):
    response = requests.get(f"{BASE_URL}/filter.php?a={area}")
    meals = response.json().get("meals") or []
    result = []
    for meal in meals[:15]:
        result.append({
            "idMeal": meal["idMeal"],
            "strMeal": meal["strMeal"],
            "strMealThumb": meal["strMealThumb"]
        })
    return result

#filter meals by ingredient
def filter_by_ingredient(ingredient):
    response = requests.get(f"{BASE_URL}/filter.php?i={ingredient}")
    meals = response.json().get("meals") or []
    result = []
    for meal in meals[:15]:
        result.append({
            "idMeal": meal["idMeal"],
            "strMeal": meal["strMeal"],
            "strMealThumb": meal["strMealThumb"]
        })
    return result

#get one random meal with full details
def get_random_meal():
    response = requests.get(f"{BASE_URL}/random.php")
    meal = response.json().get("meals", [])
    if not meal:
        return None
    return get_full_details(meal[0])

#get full details of meal by id
def get_meal_details_by_id(meal_id):
    response = requests.get(f"{BASE_URL}/lookup.php?i={meal_id}")
    meal = response.json().get("meals") or []
    if not meal:
        return None
    return get_full_details(meal[0])
    
    #handle  each client in a separate thread
def handle_client(conn, addr):
    client_name = "Unknown"

    try:
        #recive client name
        data = receive_data(conn)
        if data and data.get("type")  in ["connect", "HELLO"]: # check if the data is not None and the type of data is "connect" or "HELLO" 
            client_name = data.get("name") or data.get("payload", {}).get("username", "Unknown") # try to get the name from the "name" key first, if not exist try to get it from the "payload" key and use unknown if both keys are not exist
            print(f" New connection: {client_name} from {addr[0]}")
            send_data(conn, {
                "type": "ok",
                "message": f"Welcome {client_name}!"
                })
            
            # keep reciving requests 
            while True:
                request = receive_data(conn)
                if  request is None: # if the client disconnected or there is an error in receiving data 
                    break

                request_type = request.get("type")
                payload = request.get("payload", {}) 
                print(f"{client_name}] request: {request_type} | {payload}")
                
                # cache requests
                if request_type == "GET_CATEGORIES":
                    send_data(conn, {"status": "ok", "source": "cache", "data": referance_cache["categories"]})
                elif request_type == "GET_AREAS":
                    send_data(conn, {"status": "ok", "source": "cache", "data": referance_cache["areas"]})
                elif request_type == "GET_INGREDIENTS":
                    send_data(conn, {"status": "ok", "source": "cache", "data": referance_cache["ingredients"]})
                # recipe requests
                elif request_type == "SEARCH_NAME":
                    meals = search_by_name(payload .get("keyword", ""))
                    save_recipe_file(client_name, "search", meals)
                    send_data(conn, {"status": "ok", "source": "api", "data": meals}) #api because we get the data from api not from cache
                elif request_type == "FILTER_CATEGORY":    
                    meals = filter_by_category(payload.get("category", ""))
                    save_recipe_file(client_name, "category", meals)
                    send_data(conn, {"status": "ok", "source": "api", "data": meals})
                elif request_type == "FILTER_AREA":
                    meals = filter_by_area(payload.get("area", ""))
                    save_recipe_file(client_name, "area", meals)
                    send_data(conn, {"status": "ok", "source": "api", "data": meals})
                elif request_type == "FILTER_INGREDIENT":
                    meals = filter_by_ingredient(payload.get("ingredient", ""))
                    save_recipe_file(client_name, "ingredient", meals)
                    send_data(conn, {"status": "ok", "source": "api", "data": meals})
                elif request_type == "RANDOM_RECIPE":
                    meal = get_random_meal()
                    save_recipe_file(client_name, "random", meal)
                    send_data(conn, {"status": "ok", "source": "api", "data": meal})
                elif request_type == "GET_DETAILS":
                    meal = get_meal_details_by_id(payload.get("meal_id", ""))
                    save_recipe_file(client_name, "details", meal)
                    send_data(conn, {"status": "ok", "source": "api", "data": meal})
                elif request_type == "QUIT":
                    print(f"{client_name} disconnected")
                    break
    except Exception as e:# to catch any error  to prevent the server from  stopping and
        print(f"Error :{e}")

    finally: # close the connection when the client disconnects or there is an error
        print(f"{client_name} disconnected")
        conn.close()
# start the server
def start_server():
    

    #step 2: create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5) # allow up to 5 pending connections

    print(f"Server is running on {HOST}:{PORT}")
    print("Waiting for connections...\n")

    #step 3: keep accepting connections
    while True:
        conn, addr = server_socket.accept()

        # step 4: new thread for each client
        client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True) # use daemon=True to make the thread exit when the main thread exits
        client_thread.start()
#oop classes
#cache class to store the three reference data in memory 
# load it when the server starts and save it to file for the rest of runtime 

class Cache: #
    def __init__(self):
        self.categories = []
        self.areas = []
        self.ingredients = []
    def load_cache(self):
        load_reference_cache()
        self.categories = referance_cache["categories"]
        self.areas = referance_cache["areas"]
        self.ingredients = referance_cache["ingredients"]

# recipe api class to handle the recipe requests and get the data from the mealdb api and return it to the client in a structured format
class RecipeAPI:
    def search(self, keyword):
        return search_by_name(keyword)
    def filter_category(self, category):
        return filter_by_category(category)
    def filter_area(self, area):
        return filter_by_area(area)
    def filter_ingredient(self, ingredient):
        return filter_by_ingredient(ingredient)
    def random(self):
        return get_random_meal()
    def details(self, meal_id):
        return get_meal_details_by_id(meal_id)

#server class to handle the server operations and manage the cache and recipe api instances and start the server
class Server:
    def __init__(self):
        self.cache = Cache()
        self.api = RecipeAPI()
    def start(self):
        self.cache.load_cache()
        start_server()
        
#run the server
if __name__ == "__main__": 
    server = Server()
    server.start()
    