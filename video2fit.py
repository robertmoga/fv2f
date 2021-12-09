import os
import tqdm
import json
import struct
import argparse
import pandas as pd

import fitparse


def get_video_uuid(vid_name):
    """
    Get the fit UUID encoded in the video moov atom.
    The container structure under which the UUID is stored is the following :
     ├── moov
     │   └── udta
     │       ├── uuid

    :param vid_name: [str] path to the video file
    :return: [str] uuid
    """
    atom_container_names = ['moov', 'udta', 'uuid']

    with open(vid_name, "rb") as f:
        uuid = None
        file_size = os.path.getsize(vid_name)
        for container_name in atom_container_names:
            while f.tell() < file_size:
                value, = struct.unpack(">I", f.read(4))
                off = 4
                name = f.read(4).decode("utf-8")
                off += 4

                if name == container_name:
                    if name == 'uuid':
                        uuid = f.read(95).decode("utf-8")
                        off += 95
                    break

                f.seek(value - off, os.SEEK_CUR)

    return uuid


def parse_fit_file(fit_file_path):
    """
    Parsing the messages of the .fit file given as a parameter.

    We are looking specifically for 2 kinds of data messages.
    The camera event messages contain info about when a video starts and ends.
    While the other records may contain telemetry data.

    More resources at: https://developer.garmin.com/fit/protocol/

    :param fit_file_path: [str] path to the .fit file
    :return:
    """
    telemetry_allowed_fields = ['timestamp', 'utc_timestamp', 'position_lat', 'position_long', 'enhanced_altitude',
                      'enhanced_speed', 'speed']
    telemetry_required_fields = ['position_lat', 'position_long']
    camera_event_fields = ['camera_event_type', 'camera_file_uuid', 'timestamp']

    fitfile = fitparse.FitFile(fit_file_path,
                               data_processor=fitparse.StandardUnitsDataProcessor())
    messages = fitfile.messages
    telemetry_data = []
    camera_events_data = []

    for message in tqdm.tqdm(messages):
        if not hasattr(message, 'fields'):
            continue
        if message.name == 'camera_event':
            message_camera_events = {}
            for field in message.fields:
                if field.name in camera_event_fields:
                    message_camera_events[field.name] = field.value
            camera_events_data.append(message_camera_events)
        else:
            message_data = {}
            for field in message.fields:
                if field.name in telemetry_allowed_fields:
                    message_data[field.name] = field.value
            if set(telemetry_required_fields).issubset(set(message_data.keys())):
                telemetry_data.append(message_data)

    return camera_events_data, telemetry_data


def get_fit_file_for_video(video_path, fit_dir):
    """
    Iterate through the .fit files in the target directory,
    parses each of them and returns the parsed results of the
    one corresponding to the target video.

    :param video_path: [str] path to the target video file
    :param fit_dir: [str] path to the directory containing fit files
    :return: None
    """
    video_uuid = get_video_uuid(video_path)
    fit_file, camera_events_data, telemetry_data = None, None, None
    for fit_file in tqdm.tqdm(os.listdir(fit_dir)):
        if fit_file.endswith('.fit'):
            camera_events_data, telemetry_data = parse_fit_file(os.path.join(fit_dir, fit_file))
            camera_events_uuids = [camera_event['camera_file_uuid'] for camera_event in camera_events_data]
            if video_uuid in camera_events_uuids:
                break
    return fit_file, camera_events_data, telemetry_data


def get_telemetry_dataframe(video_path, fit_dir):
    """
    Extracting telemetry and camera data from the fit file
    corresponding to the target video.
    Trims the dataframe based on the start and end video timestamps.

    :param video_path: [str] path to the target video file
    :param fit_dir: [str] path to the directory containing fit files
    :return: dataframe
    """
    fit_file, camera_events_data, telemetry_data = get_fit_file_for_video(video_path, fit_dir)
    video_uuid = get_video_uuid(video_path)

    if video_uuid is None:
        raise IOError('Video does not contain the target uuid')

    if fit_file is None:
        raise FileNotFoundError(f'No .fit file corresponds to video uuid: {video_uuid} ')

    target_start_video_ts = [camera_event['timestamp'] for camera_event in camera_events_data
                             if camera_event['camera_file_uuid'] == video_uuid
                             and camera_event['camera_event_type'] == 'video_start'][0]

    target_end_video_ts = [camera_event['timestamp'] for camera_event in camera_events_data
                           if camera_event['camera_file_uuid'] == video_uuid
                           and camera_event['camera_event_type'] == 'video_end'][0]

    df = pd.DataFrame(telemetry_data)
    df = df.fillna(method="pad")

    return df[(df.timestamp >= target_start_video_ts) & (df.timestamp < target_end_video_ts)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    match_video_command = subparser.add_parser('get_matching_fit')
    dataframe_command = subparser.add_parser('get_video_data')

    match_video_command.add_argument('--video', type=str, required=True)
    match_video_command.add_argument('--fit_dir', type=str, required=True)

    dataframe_command.add_argument('--video', type=str, required=True)
    dataframe_command.add_argument('--fit_dir', type=str, required=True)
    dataframe_command.add_argument('--output', type=str, required=True)

    args = parser.parse_args()
    if args.command == 'get_matching_fit':
        fit_file, _, _ = get_fit_file_for_video(args.video, args.fit_dir)
        print(f'Fit file corresponding to video {os.path.split(args.video)[1]} : {fit_file}')
    if args.command == 'get_video_data':
        df = get_telemetry_dataframe(args.video, args.fit_dir)
        df.to_csv(args.output, index=False)
        print(f'Dataframe dumped at {args.output}')

