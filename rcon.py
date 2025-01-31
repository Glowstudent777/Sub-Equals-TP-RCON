import time
import logging
import requests
from mcrcon import MCRcon
import random
import re
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)

RCON_HOST = '127.0.0.1'
RCON_PASSWORD = 'password'
RCON_PORT = 25575

MINECRAFT_USERNAME = "Glowstudent"
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FETCH_INTERVAL = 20
TP_RADIUS = 100
TP_DELAY = 2


def fetch_subscriber_count():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        subscriber_count = int(
            data['items'][0]['statistics']['subscriberCount'])
        logging.info(f"Subscriber Count: {subscriber_count}")

        return subscriber_count

    except Exception as e:
        logging.error(f"Error fetching subscriber count: {e}")
        return None


def connect_rcon():
    try:
        rcon = MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT)
        rcon.connect()
        return rcon
    except Exception as e:
        logging.error(f"Failed to connect to RCON: {e}")
        return None


def send_rcon_command(command: str, rcon, get_output=False):
    try:
        response = rcon.command(command)
        return response if get_output else True
    except Exception as e:
        logging.error(f"RCON command error: {e}")
        return None


def is_safe_location(x: int, y: int, z: int, rcon):
    cmd = (f"execute positioned {x} {y} {z} "
           "if block ~ ~ ~ #rcon:walkable "
           "if block ~ ~1 ~ minecraft:air "
           "unless block ~ ~-1 ~ minecraft:air "
           "unless block ~ ~-1 ~ #rcon:unsafe"
           )

    response = send_rcon_command(cmd, rcon, True)

    if "That position is not loaded" in response:
        is_loaded = send_rcon_command(f"forceload query {x} {z}", rcon, True)
        if "is not marked" in is_loaded:
            send_rcon_command(f"forceload add {x} {z} {x} {z}", rcon)
        is_safe_location(x, y, z, rcon)

    return "passed" in response if response else False


def get_random_coordinates(player_x: int, player_z: int):
    offset_x = random.randint(-TP_RADIUS, TP_RADIUS)
    offset_z = random.randint(-TP_RADIUS, TP_RADIUS)
    return player_x + offset_x, player_z + offset_z


def get_player_coords(player: str, rcon):
    coords = send_rcon_command(f"data get entity {player} Pos", rcon, True)

    if "No entity was found" in coords:
        return None, None, None

    matches = re.findall(r"[-\d.]+(?=d)", coords)
    if len(matches) < 3:
        return None, None, None

    coords = list(map(lambda x: int(float(x)), matches))
    x, y, z = coords[0], coords[1], coords[2]

    logging.info(f"Player coordinates: {x} {y} {z}")
    return x, y, z


def find_valid_location(rcon, player: str):
    player_x, player_y, player_z = get_player_coords(player, rcon)

    if player_x is None:
        logging.error("Player not found.")
        return None, None, None

    for _ in range(30):
        new_x, new_z = get_random_coordinates(player_x, player_z)
        new_y = player_y

        logging.info("Testing {0} {1} {2}".format(
            new_x, new_y, new_z))

        if is_safe_location(new_x, new_y, new_z, rcon):
            return new_x, new_y, new_z

        for y_offset in range(-5, 10):
            if is_safe_location(new_x, new_y + y_offset, new_z, rcon):
                return new_x, new_y + y_offset, new_z

    logging.info("Could not find a valid location within 30 attempts.")
    return None, None, None


def main():
    prev_count = fetch_subscriber_count()

    while prev_count is None:
        prev_count = fetch_subscriber_count()
        logging.error(
            "Failed to fetch initial subscriber count, retrying in 20 seconds...")
        time.sleep(FETCH_INTERVAL)

    while True:
        current_count = fetch_subscriber_count()
        if current_count is not None:
            if current_count > prev_count:
                new_subs = current_count - prev_count
                logging.info(f"New subscribers detected: {new_subs}")

                rcon = connect_rcon()

                if rcon:
                    coords = find_valid_location(rcon, MINECRAFT_USERNAME)
                    if coords is not None:
                        logging.info(f"Valid coordinates found: {coords}")
                        send_rcon_command(
                            f"tp {MINECRAFT_USERNAME} {coords[0]} {coords[1]} {coords[2]}", rcon)
                    rcon.disconnect()
                else:
                    logging.error("Failed to connect to RCON.")
                prev_count = current_count
            elif current_count < prev_count:
                logging.info(
                    f"Subscriber count decreased from {prev_count} to {current_count}. No kill command issued.")
                prev_count = current_count
        else:
            logging.info("No new subscribers.")
        time.sleep(FETCH_INTERVAL)


if __name__ == '__main__':
    main()
