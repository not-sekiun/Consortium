import os
import library.modules.config as config
import library.modules.keygen as keygen

config.main()

def main():
    move_back_to = os.getcwd()
    os.chdir(config.started_at)
    dir = os.listdir(os.getcwd())
    keygen.main('user_initiated')
    os.chdir(move_back_to)