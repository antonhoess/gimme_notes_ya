#!/usr/bin/env python

from __future__ import annotations
from typing import List, Optional
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"  # noqa # Suppresses pygame console output
import tkinter as tk
import argparse
import datetime
import pandas as pd
import music21 as m21
import time
from dataclasses import dataclass
from enum import IntEnum
import signal

from midi import Midi, MidiDeviceType, MidiEvent

signal.signal(signal.SIGINT, signal.SIG_DFL)


class MidiTestBase:
    _notes = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "h"]

    @staticmethod
    def _choose_input_device(input_device_id: Optional[int]):
        # List all available MIDI input devices for the user
        print("Available MIDI input devices")
        device_ids = list()
        for device in Midi.get_midi_devices(MidiDeviceType.INPUT):
            print(f"* [{device.device_id}] \"{device.name}\" (interface: \"{device.interface}\")")
            device_ids.append(device.device_id)
        # end for

        # Let the user choose which device to use
        if input_device_id is None:
            device_id_str = ""
            while True:
                try:
                    device_id_str = input("Select input device id: ")
                    device_id = int(device_id_str)

                    if device_id in device_ids:
                        input_device_id = device_id
                        break
                    # end if

                    print(f"{device_id} is not in the list of device-IDs.")
                except ValueError:
                    print(f"\"{device_id_str}\" is not a valid number.")
                    continue
                # end try
            # end while
        # end if

        return input_device_id
    # end def

    @staticmethod
    def _choose_output_device(output_device_id: Optional[int]):
        # List all available MIDI output devices for the user
        print("Available MIDI output devices")
        device_ids = list()
        for device in Midi.get_midi_devices(MidiDeviceType.OUTPUT):
            print(f"* [{device.device_id}] \"{device.name}\" (interface: \"{device.interface}\")")
            device_ids.append(device.device_id)
        # end for

        # Let the user choose which device to use
        print("")
        if output_device_id is None:
            device_id_str = ""
            while True:
                try:
                    device_id_str = input("Select output device id: ")
                    device_id = int(device_id_str)

                    if device_id in device_ids:
                        output_device_id = device_id
                        break
                    # end if

                    print(f"{device_id} is not in the list of device-IDs.")
                except ValueError:
                    print(f"\"{device_id_str}\" is not a valid number.")
                    continue
                # end try
            # end while
        # end if

        return output_device_id
    # end def
# end class


class MidiTestPlay(MidiTestBase):
    class NoteState(IntEnum):
        ON = 1
        OFF = 2

    @dataclass
    class Note:
        start: float
        duration: float
        pitch: int
        velocity: float
        channel: int
        instrument: int
        instrument_name: str
    # end class

    @dataclass
    class NoteToggle:
        time: float
        state: MidiTestPlay.NoteState
        pitch: int
        velocity: float
        channel: int
        instrument: int
        instrument_name: str
    # end class

    def __init__(self, output_device_id: int = None, musicxml_file: Optional[str] = None, bpm: int = 120) -> None:
        self._output_device_id = self._choose_output_device(output_device_id)
        self._musicxml_file = musicxml_file
        self._bpm = bpm
        # --

        # Initialize the MIDI interface
        print(f"Initializing MIDI interface... ", end="")
        self._midi = Midi(None, self._output_device_id, None)
        print("Done")
    # end def

    def print_note_list(self, note_list: List):
        df = pd.DataFrame(
            map(lambda n: (n.time, "on" if n.state == MidiTestPlay.NoteState.ON else "off", f"{n.pitch} ({self._notes[int(n.pitch % 12)].upper() + str(n.pitch // 12 - 1)})", n.velocity, n.instrument), note_list),
            columns=["Time", "State", "Pitch (Note)", "Velocity", "Instrument"])
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        print(df)
    # end def

    def run(self, show_note_list: bool = False):
        if self._musicxml_file is not None:
            xml_data = m21.converter.parse(self._musicxml_file)
            xml_list = self._xml_to_list(xml_data)
            xml_list.sort(key=lambda n: n.start)

            note_list = list()
            for item in xml_list:
                note_list.append(MidiTestPlay.NoteToggle(item.start, MidiTestPlay.NoteState.ON, item.pitch, item.velocity, item.channel, item.instrument, item.instrument_name))
                note_list.append(MidiTestPlay.NoteToggle(item.start + item.duration, MidiTestPlay.NoteState.OFF, item.pitch, item.velocity, item.channel, item.instrument, item.instrument_name))
            # end for

            note_list.sort(key=lambda n: (n.time, n.state == MidiTestPlay.NoteState.ON))

            if show_note_list:
                self.print_note_list(note_list)

            start_time = datetime.datetime.now()

            while True:
                td = datetime.datetime.now() - start_time
                td = td.seconds + td.microseconds / 1e6

                # Handle all outstanding events
                while len(note_list) > 0:
                    note = note_list[0]
                    if td >= float(note.time) / self._bpm * 60.:
                        self._midi.play_note(note.pitch, int(note.velocity * 127), note.channel, instrument=note.instrument, off=note.state == MidiTestPlay.NoteState.OFF)
                        del note_list[0]
                    else:
                        break
                    # end if
                # end while

                # Leave when done
                if len(note_list) == 0:
                    break
                # end if

                # Polling
                time.sleep(0.01)  # 10 ms
            # end while
        # end if
    # end def

    @staticmethod
    def _xml_to_list(xml_data: str, print_part_instrument_channel_assoc: bool = False) -> List[MidiTestPlay.Note]:
        xml_list = list()

        for part in xml_data.parts:
            instrument = part.getInstrument().midiProgram
            instrument_name = part.getInstrument().instrumentName
            channel = part.getInstrument().midiChannel
            if print_part_instrument_channel_assoc:
                print(f"{part.getInstrument().midiProgram}: {part.getInstrument().midiChannel}")

            for note in part.flat.notes:
                if note.isChord:
                    start = note.offset
                    duration = note.quarterLength

                    for chord_note in note.pitches:
                        pitch = int(chord_note.ps)
                        velocity = note.volume.realized
                        xml_list.append(MidiTestPlay.Note(start, duration, pitch, velocity, channel, instrument, instrument_name))

                else:
                    start = note.offset
                    duration = note.quarterLength
                    pitch = int(note.pitch.ps)
                    velocity = note.volume.realized
                    xml_list.append(MidiTestPlay.Note(start, duration, pitch, velocity, channel, instrument, instrument_name))
                # end if
            # end for
        # end for

        return xml_list
    # end def


class MidiTestShow(MidiTestBase):
    def __init__(self, input_device_id: int = None, output_device_id: int = None, use_computer_keyboard: bool = False) -> None:
        super().__init__()
        self._input_device_id = self._choose_input_device(input_device_id)
        self._output_device_id = self._choose_output_device(output_device_id)
        self._use_computer_keyboard = use_computer_keyboard
        self._octave = 5
        self._velocity = 127
        self._start_time = datetime.datetime.now()
        # --
        self._root = None
        self._label = None
        self._computer_keyboard_keys = ("a", "w", "s", "e", "d", "f", "t", "g", "z", "h", "u", "j", "k")
        self._key_mapping = {key: k for k, key in enumerate(self._computer_keyboard_keys)}
        self._currently_pressed_keys = list()

        if self._use_computer_keyboard:
            print("Using computer keyboard.")

        # Initialize the MIDI interface
        print(f"Initializing MIDI interface... ", end="")
        self._midi = Midi(self._input_device_id, self._output_device_id, self._cb_event)
        print("Done")
    # end def

    def _cb_event(self, event: MidiEvent) -> None:
        print(event)
        self._label["text"] = self._notes[event.data1 % 12].upper()
        if self._output_device_id is not None:
            self._midi.play_note(event.data1, event.data2)
    # end def

    def _get_time_since_start(self) -> int:
        dt = datetime.datetime.now() - self._start_time
        diff = int(dt.seconds * 1000 + dt.microseconds / 1000)

        return diff
    # end def

    def _cb_key_press(self, event):
        if event.char == "y":  # One octave down
            self._octave = max(self._octave - 1, 0)

        elif event.char == "x":  # One octave up
            self._octave = min(self._octave + 1, 9)

        elif event.char == "c":  # Increase velocity
            self._velocity = max(self._velocity - 20, 0)

        elif event.char == "v":  # Increase velocity
            self._velocity = min(self._velocity + 20, 127)

        elif event.char in self._computer_keyboard_keys:
            # Prevent automatic repetition of the key_press-event by the keyboard driver
            if event.char not in self._currently_pressed_keys:
                self._currently_pressed_keys.append(event.char)
                self._cb_event(MidiEvent(0, self._octave * 12 + self._key_mapping[event.char],
                                         self._velocity, 0, self._get_time_since_start(), -1))
            # end if
        # end if
    # end def

    def _cb_key_release(self, event):
        # Switch key off by settings its velocity to 0
        if event.char in self._computer_keyboard_keys:
            self._currently_pressed_keys.remove(event.char)
            self._cb_event(MidiEvent(0, self._octave * 12 + self._key_mapping[event.char],
                                     0, 0, self._get_time_since_start(), -1))
        # end if
    # end def

    def run(self) -> None:
        # GUI
        self._root = tk.Tk()
        self._root.title("Press a key on the keyboard to show its note in the window")
        self._root.geometry("500x500")  # Width x height

        self._label = tk.Label(self._root, text="", font=("Arial", 250, ""))  # Create a text label
        self._label.pack(padx=20, pady=20)  # Pack it into the window

        if self._use_computer_keyboard:
            self._root.bind_all("<KeyPress>", self._cb_key_press)
            self._root.bind_all("<KeyRelease>", self._cb_key_release)
        # end if

        self._root.mainloop()
    # end def
# end class


class MidiTestThru(MidiTestBase):
    def __init__(self, input_device_id: int = None, output_device_id: int = None) -> None:
        super().__init__()
        self._input_device_id = self._choose_input_device(input_device_id)
        self._output_device_id = self._choose_output_device(output_device_id)
        self._start_time = datetime.datetime.now()

        # Initialize the MIDI interface
        print(f"Initializing MIDI interface... ", end="")
        self._midi = Midi(self._input_device_id, self._output_device_id, self._cb_event)
        print("Done")
    # end def

    def _cb_event(self, event: MidiEvent) -> None:
        print(event)
        if self._output_device_id is not None:
            self._midi.play_note(event.data1, event.data2)
    # end def

    def _get_time_since_start(self) -> int:
        dt = datetime.datetime.now() - self._start_time
        diff = int(dt.seconds * 1000 + dt.microseconds / 1000)

        return diff
    # end def

    def run(self) -> None:
        while True:
            time.sleep(1)
        # end while
    # end def
# end class


def main():
    # create some parent parsers
    parser_input_device_id = argparse.ArgumentParser(add_help=False)
    parser_input_device_id.add_argument("--input_device_id", type=int, required=False, default=None,
                                        help="MIDI input device ID.")

    parser_output_device_id = argparse.ArgumentParser(add_help=False)
    parser_output_device_id.add_argument("--output_device_id", type=int, required=False, default=None,
                                         help="MIDI output device ID.")

    # create the top-level parser
    # ---------------------------
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="mode",
                                       help="Mode.")

    # create the parser for the "play" command
    parser_play = subparsers.add_parser("play", aliases=["p"], parents=[parser_output_device_id],
                                        help="Play xmlmusic mode.")
    parser_play.add_argument("--musicxml_file", type=str, required=False, default=None,
                             help="The MusicXML file to play.")
    parser_play.add_argument("--bpm", type=int, required=False, default=80,
                             help="Beats per minute to play xmlmusic file.")

    # create the parser for the "show" command
    parser_show = subparsers.add_parser("show", aliases=["s"], parents=[parser_input_device_id, parser_output_device_id],
                                        help="Show keyboard events mode.")
    parser_show.add_argument("--use_computer_keyboard", type=int, required=False, default=True,
                             help="Use the computer keyboard in addition to a MIDI input device "
                                  "(especially interesting for testing purposes when no MIDI input device is available).")

    # create the parser for the "thru" command
    parser_thru = subparsers.add_parser("thru", aliases=["t"], parents=[parser_input_device_id, parser_output_device_id],
                                        help="Pass-through keyboard events mode.")

    # test command lines
    cmd_line = None
    # cmd_line = ""
    # cmd_line = r'p --output_device_id=0 --musicxml_file=notes/Interstellar.musicxml --bpm=96'
    # cmd_line = r's --input_device_id=2 --use_computer_keyboard=1'
    # cmd_line = r't --input_device_id=2 --output_device_id=5'

    if cmd_line is not None:
        if cmd_line.strip() != "":
            cmds = cmd_line.split(" ")
        else:
            cmds = list()
        args = parser.parse_args(cmds)
    else:
        args = parser.parse_args()

    if args.mode in ["p", "play"]:
        MidiTestPlay(args.output_device_id, args.musicxml_file, bpm=args.bpm).run(show_note_list=False)

    elif args.mode in ["s", "show"]:
        MidiTestShow(args.input_device_id, args.output_device_id, args.use_computer_keyboard).run()

    elif args.mode in ["t", "thru"]:
        MidiTestThru(args.input_device_id, args.output_device_id).run()
# end def


if __name__ == "__main__":
    main()
# end if
