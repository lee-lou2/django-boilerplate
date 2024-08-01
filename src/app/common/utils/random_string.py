import random
import string


def get_random_string(length):
    characters = string.ascii_lowercase + string.digits
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string
