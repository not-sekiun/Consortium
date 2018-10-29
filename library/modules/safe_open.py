import os


def main(path, mode):
    dir = os.path.dirname(path)
    if os.path.isdir(dir):
        return open(path, mode)
    else:
        os.makedirs(os.path.dirname(path))
        return open(path, mode)
