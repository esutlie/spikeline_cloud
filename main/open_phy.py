import os


def open_phy(save_folder):
    anaconda_prompt_cmd = ' '.join([os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3', 'Scripts', 'activate.bat'),
                                    os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3')])
    folder_path = f'cd /d D:\\SpikeInterface\\spike_interface\\{save_folder}'
    os.system(
        r"""start "My Spyder Package Installer" /wait cmd /c "%s&%s&%s&%s" """ % (
            anaconda_prompt_cmd, 'conda activate phy2', folder_path, 'phy template-gui params.py'))


if __name__ == '__main__':
    open_phy('phy_folder_for_ironclust0')
