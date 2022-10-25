import os
from process_functions import *


def extract_waveforms(sorter=None, recording=None, file_path=None):
    if sorter and recording:
        current_dir = os.path.dirname(os.getcwd())
        if not file_path:
            file_path = reset_folder(os.path.join(current_dir, 'waveforms'), local=False)
        waveforms = si.WaveformExtractor.create(recording, sorter, file_path)
        waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
        waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
    elif file_path:
        waveforms = si.WaveformExtractor.load_from_folder(file_path)
        waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
        waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
    else:
        print('need to pass either a file_path or a sorter/recording pair to extract_waveforms()')
        raise Exception
    return waveforms
