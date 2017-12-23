import random

def rand_string(length):
    possible_chars = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890!@#$%^&*()-=[];,./_+{}|:"<>?'
    random_strings = ''
    for i in range(length):
        random_strings += random.choice(possible_chars)
    return random_strings