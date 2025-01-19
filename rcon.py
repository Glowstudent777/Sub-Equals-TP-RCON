import time
import logging
import requests
from mcrcon import MCRcon
import random

logging.basicConfig(level=logging.INFO)

RCON_HOST = '127.0.0.1'
RCON_PASSWORD = 'password'
RCON_PORT = 25575
API_KEY = ''
CHANNEL_ID = ''

FETCH_INTERVAL = 20
TP_RADIUS = 100
TP_DELAY = 2


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
        logging.info(f"RCON Response: {response}")
        return response if get_output else True
    except Exception as e:
        logging.error(f"RCON command error: {e}")
        return None


def test_block(x: int, y: int, z: int, rcon, block_tag: str):
    cmd = f"execute positioned {x} {y} {z} if block ~ ~ ~ {block_tag}"

    if "That position is not loaded" in (send_rcon_command(cmd, rcon, True) or ""):
        is_loaded = send_rcon_command(f"forceload query {x} {z}", rcon, True)
        if "is not marked" in is_loaded:
            send_rcon_command(f"forceload add {x} {z} {x} {z}", rcon)
        test_block(x, y, z, rcon, block_tag)

    return "passed" in (send_rcon_command(cmd, rcon, True) or "")


def get_random_coordinates(player_x: int, player_z: int):
    offset_x = random.randint(-TP_RADIUS, TP_RADIUS)
    offset_z = random.randint(-TP_RADIUS, TP_RADIUS)
    return player_x + offset_x, player_z + offset_z


def test_valid_location(x: int, y: int, z: int, rcon):
    has_block_below = test_block(
        x, y - 1, z, rcon, "minecraft:air") is False and test_block(x, y - 1, z, rcon, "#rcon:unsafe") is False
    is_safe = (test_block(x, y, z, rcon, "minecraft:air")
               and test_block(x, y + 1, z, rcon, "minecraft:air"))

    return has_block_below and is_safe


def get_player_coords(player: str, rcon):
    coords = send_rcon_command(f"data get entity {player} Pos", rcon, True)

    if "No entity was found" in coords:
        return None, None, None

    coords = coords.split(" ")
    return int(float(coords[0])), int(float(coords[1])), int(float(coords[2]))


def find_valid_location(rcon, player: str):
    found_location = False
    player_x, player_y, player_z = get_player_coords(player, rcon)

    if player_x is None:
        player_x, player_y, player_z = 0, 63, 0

    for _ in range(50):
        if found_location:
            break

        new_x, new_z = get_random_coordinates(player_x, player_z)
        new_y = player_y

        if test_valid_location(new_x, new_y, new_z, rcon):
            found_location = True
            break

        for y_offset in range(0, 256):
            new_y = player_y + y_offset
            if test_valid_location(new_x, new_y, new_z, rcon):
                found_location = True
                break

    if not found_location:
        logging.warning("Could not find a valid location within 50 attempts.")
        return None, None, None
    else:
        print(f"Teleporting to {new_x}, {new_y}, {new_z}")
        return new_x, new_y, new_z


def main():
    while True:
        rcon = connect_rcon()

        if rcon is not None:
            coords = find_valid_location(rcon, "Glowstudent")

            if coords != (None, None, None):
                logging.info(f"Valid coordinates found: {coords}")
            rcon.disconnect()

        time.sleep(FETCH_INTERVAL)


if __name__ == '__main__':
    main()
