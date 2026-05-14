# ============================================================
# client.py  —  Recipe Discovery System (Client Side)
# ITNE352: Network Programming  |  S2 2025-2026
# Group: B4
# ============================================================

import socket
import sys
import os

# ── Import shared protocol ───────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from protocol import (
    send_message, receive_message,
    REQ_CATEGORIES, REQ_AREAS, REQ_INGREDIENTS,
    REQ_SEARCH, REQ_FILTER_CAT, REQ_FILTER_AREA,
    REQ_FILTER_ING, REQ_RANDOM, REQ_DETAILS, REQ_QUIT,
    VALID_CATEGORIES, VALID_AREAS
)

# ── Connection settings ──────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


# ============================================================
# FIX 1 — extract_name()
# ============================================================
def extract_name(item: dict) -> str:
    """
    The API returns reference items as dicts with ONE name key:
      categories  -> {"strCategory": "Beef"}
      areas       -> {"strArea": "Italian"}
      ingredients -> {"strIngredient": "Garlic"}

    We try each key and return the first non-empty value found.
    """
    for key in ("strCategory", "strArea", "strIngredient"):
        value = item.get(key, "").strip()
        if value:
            return value
    return str(item)   # fallback


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_header(title: str) -> None:
    width = 58
    print("\n" + "=" * width)
    print(f"  {title.upper()}")
    print("=" * width)


def print_divider() -> None:
    print("-" * 58)


def print_recipe_brief(index: int, meal: dict) -> None:
    print(f"  {index:>2}. {meal.get('strMeal', 'Unknown')}")
    print(f"      ID    : {meal.get('idMeal', '?')}")
    print(f"      Thumb : {meal.get('strMealThumb', 'N/A')}")


def print_recipe_details(meal: dict) -> None:
    """
    Print full recipe details.
    The server sends ingredients as a list of plain strings
    e.g. ["1 cup Flour", "2 tsp Salt"] — we just iterate them.
    """
    print_header(meal.get("strMeal", "Recipe Details"))

    print(f"  Category : {meal.get('strCategory', 'N/A')}")
    print(f"  Area     : {meal.get('strArea',     'N/A')}")
    print(f"  Tags     : {meal.get('strTags')  or 'None'}")
    print(f"  YouTube  : {meal.get('strYoutube') or 'N/A'}")
    print(f"  Source   : {meal.get('strSource')  or 'N/A'}")

    # Ingredients — server sends a pre-built list of strings
    print_divider()
    print("  INGREDIENTS:")
    ingredients = meal.get("ingredients", [])
    if ingredients:
        for ing in ingredients:
            print(f"    *  {ing}")
    else:
        print("    (no ingredients found)")

    # Instructions
    print_divider()
    print("  INSTRUCTIONS:")
    instructions = meal.get("strInstructions", "N/A")
    for line in instructions.split("\n"):
        line = line.strip()
        if line:
            while len(line) > 75:
                print(f"    {line[:75]}")
                line = line[75:]
            print(f"    {line}")

    print_divider()


# ============================================================
# INPUT HELPERS
# ============================================================

def pick_from_list(label: str, options: list) -> str:
    print(f"\n  Available {label}:")
    for i, item in enumerate(options, start=1):
        print(f"    {i:>2}. {item}")
    while True:
        choice = input(f"\n  Enter number (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("  [!] Invalid choice — enter a number from the list.")


def get_keyword(prompt: str) -> str:
    while True:
        value = input(f"  {prompt}: ").strip()
        if value:
            return value
        print("  [!] Input cannot be empty.")


# ============================================================
# MENUS
# ============================================================

def show_main_menu() -> str:
    print_header("Recipe Discovery System — Main Menu")
    print("  1.  Browse Recipes")
    print("  2.  Reference Lists")
    print("  3.  Quit")
    print_divider()
    return input("  Your choice: ").strip()


def show_recipes_menu() -> str:
    print_header("Browse Recipes")
    print("  1.1  Search by name")
    print("  1.2  Filter by category")
    print("  1.3  Filter by area")
    print("  1.4  Filter by ingredient")
    print("  1.5  Random recipe")
    print("  1.6  Back to main menu")
    print_divider()
    return input("  Your choice: ").strip()


def show_reference_menu() -> str:
    print_header("Reference Lists")
    print("  2.1  List all categories")
    print("  2.2  List all areas")
    print("  2.3  List all ingredients  (first 50)")
    print("  2.4  Back to main menu")
    print_divider()
    return input("  Your choice: ").strip()


# ============================================================
# FIX 1 APPLIED HERE — display_reference_list
# ============================================================
def display_reference_list(response: dict, label: str) -> None:
    """
    BUG (before fix):
        print(item)
        --> {'strCategory': 'Beef'}   <-- prints the whole dict!

    FIX:
        print(extract_name(item))
        --> Beef                      <-- clean name only
    """
    data = response.get("data", [])
    if not data:
        print("\n  (no results received)")
        return

    print_header(f"{label}  --  {len(data)} items")
    for i, item in enumerate(data, start=1):
        # item is a dict like {"strCategory": "Beef"}
        if isinstance(item, dict):
            name = extract_name(item)   # <-- THE FIX
        else:
            name = str(item)            # already a plain string
        print(f"  {i:>3}.  {name}")
    print_divider()


# ============================================================
# RECIPE LIST + DRILL-DOWN TO DETAILS
# ============================================================
def display_recipe_list_and_ask(sock: socket.socket,
                                 response: dict) -> None:
    meals = response.get("data", [])
    if not meals:
        print("\n  No recipes found — try a different search.")
        return

    print_header(f"Results  --  {len(meals)} recipe(s) found")
    for i, meal in enumerate(meals, start=1):
        print_recipe_brief(i, meal)
        print_divider()

    print(f"\n  Enter a number for full details (1-{len(meals)}),")
    print("  or press Enter to go back.")
    choice = input("  Your choice: ").strip()

    if not choice:
        return

    if choice.isdigit() and 1 <= int(choice) <= len(meals):
        meal_id = meals[int(choice) - 1].get("idMeal")
        send_message(sock, {
            "type": REQ_DETAILS,
            "payload": {"meal_id": meal_id}
        })
        details = receive_message(sock)
        if details.get("status") == "ok":
            print_recipe_details(details.get("data", {}))
        else:
            print(f"\n  [!] Server error: {details.get('message')}")
    else:
        print("  [!] Invalid number — going back.")


# ============================================================
# RECIPES MENU HANDLER
# ============================================================
def handle_recipes_menu(sock: socket.socket) -> None:
    while True:
        choice = show_recipes_menu()

        if choice == "1.1":
            keyword = get_keyword("Enter recipe name or keyword")
            send_message(sock, {
                "type": REQ_SEARCH,
                "payload": {"keyword": keyword}
            })
            display_recipe_list_and_ask(sock, receive_message(sock))

        elif choice == "1.2":
            category = pick_from_list("Categories", VALID_CATEGORIES)
            send_message(sock, {
                "type": REQ_FILTER_CAT,
                "payload": {"category": category}
            })
            display_recipe_list_and_ask(sock, receive_message(sock))

        elif choice == "1.3":
            area = pick_from_list("Areas / Cuisines", VALID_AREAS)
            send_message(sock, {
                "type": REQ_FILTER_AREA,
                "payload": {"area": area}
            })
            display_recipe_list_and_ask(sock, receive_message(sock))

        elif choice == "1.4":
            raw = get_keyword("Enter ingredient (e.g. chicken, garlic)")
            ingredient = raw.strip().replace(" ", "_")
            send_message(sock, {
                "type": REQ_FILTER_ING,
                "payload": {"ingredient": ingredient}
            })
            display_recipe_list_and_ask(sock, receive_message(sock))

        elif choice == "1.5":
            send_message(sock, {"type": REQ_RANDOM})
            response = receive_message(sock)
            if response.get("status") == "ok":
                print_recipe_details(response.get("data", {}))
            else:
                print(f"\n  [!] {response.get('message')}")

        elif choice == "1.6":
            break

        else:
            print("\n  [!] Invalid option — choose 1.1 to 1.6.")


# ============================================================
# REFERENCE MENU HANDLER
# ============================================================
def handle_reference_menu(sock: socket.socket) -> None:
    while True:
        choice = show_reference_menu()

        if choice == "2.1":
            send_message(sock, {"type": REQ_CATEGORIES})
            display_reference_list(receive_message(sock), "Meal Categories")

        elif choice == "2.2":
            send_message(sock, {"type": REQ_AREAS})
            display_reference_list(receive_message(sock), "Areas / Cuisines")

        elif choice == "2.3":
            send_message(sock, {"type": REQ_INGREDIENTS})
            response = receive_message(sock)
            response["data"] = response.get("data", [])[:50]  # limit to first 50
            display_reference_list(response, "Ingredients")

        elif choice == "2.4":
            break

        else:
            print("\n  [!] Invalid option — choose 2.1 to 2.4.")


# ============================================================
# MAIN
# ============================================================
def main():
    print("\n" + "=" * 58)
    print("   Welcome to the Recipe Discovery System")
    print("=" * 58)

    username = get_keyword("Enter your username")

    print(f"\n  Connecting to {SERVER_HOST}:{SERVER_PORT} ...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print("  Connected!\n")
    except ConnectionRefusedError:
        print("\n  [ERROR] Cannot connect — is the server running?")
        sys.exit(1)

    # Send username to server
    send_message(sock, {
        "type": "HELLO",
        "payload": {"username": username}
    })
    greeting = receive_message(sock)
    print(f"  Server: {greeting.get('message', 'Hello!')}\n")

    try:
        while True:
            choice = show_main_menu()
            if choice == "1":
                handle_recipes_menu(sock)
            elif choice == "2":
                handle_reference_menu(sock)
            elif choice == "3":
                send_message(sock, {"type": REQ_QUIT})
                print("\n  Goodbye!\n")
                break
            else:
                print("\n  [!] Please choose 1, 2, or 3.")
    finally:
        sock.close()
        print("  Connection closed.\n")


if __name__ == "__main__":
    main()
