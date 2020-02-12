import re

def CommandStrip(message):
    return re.sub(r'^(\?\w*)', '', message)