import shutil
import os


def main(path):
    print '[*]Initiating compilation of scout : ' + path
    tags = []
    while True:
        option = raw_input('[>]Compress compiled scout into one file? [y|n] : ')
        if option in ('y', 'Y', 'yes', 'Yes'):
            tags.append('--onefile')
            break
        elif option in ('n', 'N', 'No', 'no'):
            break
        else:
            continue
    while True:
        option = raw_input('[>]Compile scout so that it runs without a window? [y|n] : ')
        if option in ('y', 'Y', 'yes', 'Yes'):
            tags.append('--windowed')
            break
        elif option in ('n', 'N', 'No', 'no'):
            break
        else:
            continue
    continue_on = raw_input(
        '[!]Reminder : compiling a scout deletes any other compiled scouts already in the "compiled" directory [Enter to continue]')
    command = 'pyinstaller ' + ' '.join(tags) + ' ' + path
    print '[*]Removing residue folders...'
    if os.path.isdir(os.path.join(os.getcwd(), 'build')):
        shutil.rmtree('build')
    if os.path.isdir(os.path.join(os.getcwd(), 'dist')):
        shutil.rmtree('dist')
    if os.path.isdir(os.path.join(os.getcwd(), 'compiled')):
        shutil.rmtree('compiled')
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
    print '[*]Compiling file...'
    os.system(command)
    if os.path.isdir(os.path.join(os.getcwd(), 'build')):
        shutil.rmtree('build')
    else:
        print '[-]Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)'
        return
    if os.path.isdir(os.path.join(os.getcwd(), 'dist')):
        os.rename(os.path.join(os.getcwd(), 'dist'), 'compiled')
    else:
        print '[-]Error, could not successfully compile scout (Is "pyinstaller" installed and visible in your PATH?)'
        return
    for i in os.listdir(os.getcwd()):
        if i.endswith('.spec'):
            os.remove(i)
    print '[+]Successfully compiled scout to : ' + os.path.join(os.getcwd(), 'compiled')
