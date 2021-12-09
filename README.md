# Fit video2fit

Fit video2fit is a utility tool aiming at pairing video produced by Garmin VIRB cameras with the right .fit file.


.fit is a format designed by Garmin to store and share information acquired from multiple sensors, on the same timeline.

In comparison with other cameras that produce a metadata file for each video, a Garmin camera will create a fit file at every startup and it can store information related multiple videos in the same file. Therefore matching a video to a fit file  becomes a challenge untackled by other fit parsing libraries.

More information about the .fit format on [Fit Protocol](https://developer.garmin.com/fit/protocol/)
* **

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.
```bash
pip install -r requirements.txt
```
   * ** 

## Usage
The utility tool has 2 commands :
   * `get_matching_fit` that finds the right .fit file for the target video. 
     Params: 
       * `video`: target video file path
       * `fit_dir`: path to directory containing the fit files
   * `get_video_data` creates a dataframe containing the sensor data acquired during the target video and dumps it as a `csv` file. Params:
       * `video`: target video file path
       * `fit_dir`: path to directory containing the fit files
       * `output`: location of the output
     
```bash
python3 fit2video.py get_matching_fit --video /data/VIRB0001.mp4 --fit_dir /data/fit_files 
```

```bash
python3 fit2video.py get_video_data --video /data/VIRB0001.mp4 --fit_dir /data/fit_files --output /data/output_df.csv
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

