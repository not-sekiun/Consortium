import os

def main():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('tput reset')