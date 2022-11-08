import os
import spikeinterface.full as si
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.comparison as sc

FOLDER_NAME = os.getenv("FOLDER_NAME", 0)

def cloud_sort(path):
    temp_recording_folder = generate_cloud_temp_folder()  # Place holder
    temp_kilosort3_folder = generate_cloud_temp_folder()  # Place holder
    temp_kilosort2_5_folder = generate_cloud_temp_folder()  # Place holder
    temp_waveforms_folder = generate_cloud_temp_folder()  # Place holder
    temp_phy_folder = generate_cloud_temp_folder()  # Place holder

    recording = se.read_spikeglx(path, stream_id='imec0.ap')

    recording_cmr = recording
    recording_f = si.bandpass_filter(recording, freq_min=300, freq_max=6000)
    recording_cmr = si.common_reference(recording_f, reference='local', operator='median', local_radius=(30, 200))
    kwargs = {'n_jobs': 8, 'total_memory': '8G'}
    recording_preprocessed = recording_cmr.save(format='binary', folder=temp_recording_folder, **kwargs)

    sorter_params = {"keep_good_only": True}
    ks3_sorter = ss.run_sorter(sorter_name='kilosort3', recording=recording, output_folder=temp_kilosort3_folder,
                               verbose=False, docker_image=True, **sorter_params)
    sorter_params = {"keep_good_only": False}
    ks2_5_sorter = ss.run_sorter(sorter_name='kilosort2_5', recording=recording, output_folder=temp_kilosort2_5_folder,
                                 verbose=False, docker_image=True, **sorter_params)

    consensus = sc.compare_multiple_sorters(sorting_list=[ks3_sorter, ks2_5_sorter],
                                            name_list=['kilosort3', 'kilosort2_5'], verbose=False,
                                            delta_time=.2,
                                            match_score=.3,
                                            spiketrain_mode='union')
    consensus = consensus.get_agreement_sorting(minimum_agreement_count=2)

    waveforms = si.WaveformExtractor.create(recording_preprocessed, consensus, temp_waveforms_folder)
    waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
    waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
    sparsity_dict = dict(method="radius", radius_um=50, peak_sign='both')

    se.export_to_phy(waveforms, temp_phy_folder, compute_pc_features=False, compute_amplitudes=False, copy_binary=False,
                     remove_if_exists=True, sparsity_dict=sparsity_dict, max_channels_per_template=None)


if __name__ == '__main__':
    path = os.path.join(FOLDER_NAME)
    cloud_sort(path)

"""
in terminal at containing folder i ran this:

gcloud builds submit --pack image=gcr.io/spikeline/test-sort

which builds the container.

then i ran this:

gcloud beta run jobs create job-testsort \
    --image gcr.io/spikeline/test-sort \
    --tasks 1 \
    --set-env-vars FOLDER_NAME="ES029_2022-09-14_bot72_0_g0" \
    --max-retries 5 \
    --region us-central1

which creates the job.

Next i ran this to run the job:

gcloud beta run jobs execute job-testsort
"""