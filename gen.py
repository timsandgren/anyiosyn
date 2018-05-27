import sys
import json
import array
import collections
import datetime

from lib.compose import sequences
from lib.compose import misc

from lib.audio import synthesis
from lib.audio import rendering

# ---------------------------------------------------------------------------------------------------------

with open('data/scales.json') as data:
    scales = json.load(data)

# ---------------------------------------------------------------------------------------------------------

def render(song_comp, file_path='audio.wav'):
    audioframes_comp = []
    fm_syn = synthesis.Osc(song_comp['meta']['sample_rate'], note_range=10000)
    note_durations = misc.note_durations(song_comp['meta']['bpm'], 128)
    note_cache = {}
    
    for t in song_comp['tracks']:
        track_audio_data = array.array('h')
        print("Rendering: " + str(t))

        note_len = t['note_length']
        note_floor = t['note_floor']
        fm_amount = t['fm_amount']

        for n in t['notes']:
            note_val = note_floor + n

            if note_val in note_cache.keys():
                note_audio = note_cache[note_val]
            else:
                note_audio = fm_syn.render_note(
                    note_val, note_durations[note_len], fm_amount=fm_amount)

                note_cache[note_val] = note_audio
            track_audio_data += note_audio
        audioframes_comp.append(track_audio_data)
    
    frame_limit = int((song_comp['meta']['duration'] * 2) * song_comp['meta']['sample_rate'])
    mixed_frames = rendering.mix_frames(audioframes_comp, frame_limit)
    rendering.write_audio(file_path, mixed_frames)
    

def compose(conf):
    comp = { 'meta': conf, 'tracks': [] }

    note_durations = misc.note_durations(conf['bpm'], 128)
    max_note_count = int((conf['duration'] * 1000) / note_durations[conf['sequence_resolution']])
    input_data_path = __file__ if 'input_data_path' not in conf.keys() else conf['input_data_path']

    # root_seq = sequences.mandelbrot_seq(max_note_count)
    # root_seq = sequences.prime_seq(max_note_count)
    # root_seq = sequences.fibonacci_seq(max_note_count)
    # root_seq = sequences.recaman_seq(max_note_count)
    root_seq = sequences.data_seq(input_data_path, max_note_count)

    for t in conf['tracks']:
        track_spec = conf['tracks'][t]

        scale = scales['CHROMATIC'] if "scale" not in track_spec.keys() else scales[track_spec['scale']]
        note_length = 16 if 'note_length' not in track_spec.keys() else track_spec['note_length']
        note_floor = 12 if 'note_floor' not in track_spec.keys() else track_spec['note_floor']
        fm_amount = 1 if 'fm_amount' not in track_spec.keys() else track_spec['fm_amount']

        serial_seq = sequences.split_seq(root_seq)
        seq_sample = misc.sample_sequence(serial_seq[:max_note_count], int(conf['sequence_resolution'] / note_length))
        scaled_seq = sequences.seq_to_scale(seq_sample, scale, destall=True)

        track = {
            'note_length': note_length, 'notes': scaled_seq, 
            'note_floor':note_floor, 'fm_amount':fm_amount
        }

        comp['tracks'].append(track)

    return comp


# ---------------------------------------------------------------------------------------------------------

def main(order_path):
    with open(order_path) as data:
        conf = json.load(data)
    
    comp = compose(conf)
    file_name = conf['filename'] + '_' + str(datetime.datetime.now())

    if conf['write_comp']:
        file_path = conf['output_data_path'] + file_name + '.json'

        with open(file_path, 'w') as fp:
            json.dump(comp, fp, sort_keys = True, indent = 4)

    if conf['write_audio']:
        file_path = conf['output_data_path'] + file_name + '.wav'
        render(comp, file_path)


if __name__ == '__main__':
    main(sys.argv[1])