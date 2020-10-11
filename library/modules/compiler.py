import os
import shutil
import library.modules.config as config

config.main()


def main():
    local_dir = os.getcwd()
    if os.name == 'nt':
        filename = 'payload.exe'
    else:
        filename = 'payload'
    print(config.inf + 'Initiating compilation of scout at directory : ' + local_dir)
    tags = []
    while True:
        option = input(config.pro + 'Compress compiled scout into one file? [y|n] : ')
        if option == 'y':
            tags.append('--onefile')
            break
        elif option == 'n':
            break
        else:
            continue
    while True:
        option = input(config.pro + 'Compile scout so that it runs without a window? [y|n] : ')
        if option == 'y':
            tags.append('--windowed')
            break
        elif option == 'n':
            break
        else:
            continue
    while True:
        option = input(config.pro + 'Use a custom file icon (.ico) for the compiled scout? [y|n] : ')
        if option == 'y':
            option = input(config.pro + 'Path to file ico or press [enter] to use the default PyIris provided windows service icon (resources/windows_service.ico) : ')
            if not option:
                option = os.path.join(config.started_at, 'resources', 'windows_service.ico')
            tags.append('--icon ' + option)
            break
        elif option == 'n':
            break
        else:
            continue
    command = 'pyinstaller ' + ' '.join(tags) + ' payload.py'
    print(config.inf + 'Removing residue folders...')
    for i in ['build', 'dist', '__pycache__']:
        if os.path.isdir(os.path.join(os.getcwd(), i)):
            shutil.rmtree('build')
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
    print(config.inf + 'Compiling file...')
    os.system(command)
    # remove garbage dirs and copy compiled exe out of dist into the root//local_datetime folder
    if os.path.isdir(os.path.join(os.getcwd(), 'build')):
        shutil.rmtree('build')
    else:
        print(config.neg + 'Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)')
        return
    if os.path.isdir(os.path.join(os.getcwd(), 'dist')):
        shutil.copy(os.path.join(os.getcwd(), 'dist', filename), os.path.join(os.getcwd(), filename))
        shutil.rmtree('dist')
        print(config.pos + 'Successfully compiled single file scout to : ' + os.path.join(os.getcwd(), filename))
    else:
        print(config.neg + 'Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)')
        return
    if os.path.isdir(os.path.join(os.getcwd(), '__pycache__')):
        shutil.rmtree('__pycache__')
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
