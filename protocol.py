

import json    # to convert Python dict ↔ JSON string
import socket  # for the type hint only




# Reference requests (served from server cache)
REQ_CATEGORIES  = "GET_CATEGORIES"   # list all categories
REQ_AREAS       = "GET_AREAS"        # list all areas/cuisines
REQ_INGREDIENTS = "GET_INGREDIENTS"  # list all ingredients

# Recipe requests (fetched live from TheMealDB)
REQ_SEARCH      = "SEARCH_NAME"      # search by keyword
REQ_FILTER_CAT  = "FILTER_CATEGORY"  # filter by category
REQ_FILTER_AREA = "FILTER_AREA"      # filter by area
REQ_FILTER_ING  = "FILTER_INGREDIENT"# filter by ingredient
REQ_RANDOM      = "RANDOM_RECIPE"    # get one random recipe
REQ_DETAILS     = "GET_DETAILS"      # get full details by meal ID

# Control messages
REQ_QUIT        = "QUIT"             # client is disconnecting


# ──────────────────────────────────────────────
# PERMITTED PARAMETER VALUES
# The client validates user input against these
# before sending a request to the server.
# ──────────────────────────────────────────────

VALID_CATEGORIES = [
    "Beef", "Chicken", "Seafood", "Vegetarian",
    "Dessert", "Pasta", "Breakfast"
]

VALID_AREAS = [
    "Italian", "Indian", "Mexican", "Japanese",
    "Moroccan", "British", "American", "Thai"
]




DELIMITER = "\n"   # marks the end of every message


def send_message(sock: socket.socket, message: dict) -> None:
    """
    Convert a Python dict to a JSON string and send it
    over the socket, ending with the DELIMITER.

    Example:
        send_message(sock, {"type": REQ_RANDOM})
    """
    # dict → JSON string → add newline → encode to bytes
    raw = json.dumps(message) + DELIMITER
    sock.sendall(raw.encode("utf-8"))


def receive_message(sock: socket.socket) -> dict:
    """
    Read bytes from the socket until we see the DELIMITER,
    then decode and parse the JSON back into a Python dict.

    Returns the parsed dict, or raises an exception if the
    connection was closed or the data was malformed.
    """
    buffer = ""                        # accumulate incoming characters
    while True:
        chunk = sock.recv(4096).decode("utf-8")   # read up to 4 KB
        if not chunk:
            # The other side closed the connection
            raise ConnectionError("Connection closed by remote host.")
        buffer += chunk
        if DELIMITER in buffer:
            # We have a complete message — stop reading
            break

    # Split on the delimiter and take the first complete message
    message_str = buffer.split(DELIMITER)[0]
    return json.loads(message_str)     # JSON string → Python dict
