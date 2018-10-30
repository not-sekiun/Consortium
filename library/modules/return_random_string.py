import random


def main(length):
    sample_space = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
    chosen = []
    for i in range(length):
        chosen.append(random.choice(sample_space))
    return ''.join(chosen)
