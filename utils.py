import random
import string


def create_short_url():
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(5)])
