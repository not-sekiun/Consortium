def main(dictionary, target):
    for key, val in dictionary.items():
        if val == target:
            return key
    return None