<h3 align="center">spikeline</h3>
  <p align="center">
    Spike sorting pipeline for generating consensus units from neuropixel recordings.

  </p>
</div>


<!-- ABOUT THE PROJECT -->
## About The Project

This is the postprocessing pipeline used by the Shuler lab to extract spike times from ephys recordings collected with Neuropixel Probes. It uses Spike Interface to run multiple sorting algorithms and find consensus units.


<!-- GETTING STARTED -->
## Installation

Requirements
* Spike Interface (https://github.com/SpikeInterface)
* Kilosort 2.5 (https://github.com/MouseLand/Kilosort/releases/tag/v2.5)
* Kilosort 3 (https://github.com/MouseLand/Kilosort)

Follow install and requirements instructions from the Spike Interface and Kilosort Readme files.

Clone the repo
   ```sh
   git clone https://github.com/esutlie/spikeline.git
   ```

Change the directories to point to your installations of Kilosort 2.5 and Kilosort3

  ```sh
  os.environ['KILOSORT3_PATH'] = os.path.join('PATH', 'TO', 'Kilosort3')
  os.environ['KILOSORT2_5_PATH'] = os.path.join('PATH', 'TO', 'Kilosort2_5')
  ```
Change the ```path``` variable to point to the folder containing your recording data

  ```sh
  if __name__ == '__main__':
      path = os.path.join('PATH', 'TO', 'RECORDINGS')
      batch_sort(path)
  ```

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.



<!-- CONTACT -->
## Contact

Elissa Sutlief - elissasutlief@gmail.com

Project Link: [https://github.com/esutlie/spikeline](https://github.com/esutlie/spikeline)


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [https://github.com/SpikeInterface](https://github.com/SpikeInterface)
* [https://github.com/MouseLand/Kilosort](https://github.com/MouseLand/Kilosort)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
