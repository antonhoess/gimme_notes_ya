import pygame
import pygame.midi
from enum import Enum
from typing import Optional, List, Callable
import threading


class MidiDeviceType(Enum):
    INPUT = 0
    OUTPUT = 1
# end if


class MidiDeviceInfo:
    # interface: string describing the device interface (e.g. 'ALSA')
    # name: string name of the device (e.g. 'Midi Through Port-0')
    # is_input: 1 if the device is an input device, otherwise 0
    # is_output: 1 if the device is an output device, otherwise 0
    # is_opened: 1 if the device is opened, otherwise 0

    def __init__(self, device_id: int, interface: str, name: str, is_input: bool, is_output: bool, is_opened: bool) -> None:
        self._device_id = device_id
        self._interface = interface
        self._name = name
        self._is_input = is_input
        self._is_output = is_output
        self._is_opened = is_opened
    # end def

    def __repr__(self) -> str:
        return f"MidiDeviceInfo(interface={self._interface}, name={self._name}, is_input={self._is_input}, " \
               f"is_output={self._is_output}, is_opened={self._is_opened})"
    # end def

    def __str__(self) -> str:
        return repr(self)
    # end if

    @property
    def device_id(self) -> int:
        return self._device_id
    # end if

    @property
    def interface(self) -> str:
        return self._interface
    # end if

    @property
    def name(self) -> str:
        return self._name
    # end if

    @property
    def is_input(self) -> bool:
        return self._is_input
    # end if

    @property
    def is_output(self) -> bool:
        return self._is_output
    # end if

    @property
    def is_opened(self) -> bool:
        return self._is_opened
    # end if
# end class


class MidiEvent:
    def __init__(self, status: int, data1: int, data2: int, data3: int, timestamp: int, device_id: int) -> None:
        self._status = status
        self._data1 = data1
        self._data2 = data2
        self._data3 = data3
        self._timestamp = timestamp
        self._device_id = device_id
    # end def

    def __repr__(self) -> str:
        return f"MidiEvent(status={self._status}, data1={self._data1}, data2={self._data2}, " \
               f"data3={self._data3}, timestamp={self._timestamp}, device_id={self._device_id})"
    # end def

    def __str__(self) -> str:
        return repr(self)
    # end if

    @property
    def status(self) -> int:
        return self._status
    # end if

    @property
    def data1(self) -> int:
        return self._data1
    # end if

    @property
    def data2(self) -> int:
        return self._data2
    # end if

    @property
    def data3(self) -> int:
        return self._data3
    # end if

    @property
    def timestamp(self) -> int:
        return self._timestamp
    # end if

    @property
    def device_id(self) -> int:
        return self._device_id
    # end if
# end class


class Midi(threading.Thread):
    def __init__(self, midi_input_device_id: Optional[int] = None, midi_output_device_id: Optional[int] = None, cb_event: Optional[Callable[[MidiEvent], None]] = None) -> None:
        super().__init__()

        Midi._init_midi()

        self._cb_event = cb_event
        self._midi_input_device_id = midi_input_device_id
        self._midi_output_device_id = midi_output_device_id
        self._input_device = pygame.midi.Input(self._midi_input_device_id) if self._midi_input_device_id is not None else None  # Open a specific midi input device
        self._output_device = pygame.midi.Output(self._midi_output_device_id) if self._midi_output_device_id is not None else None  # Open a specific midi output device

        # Start the thread
        self.start()
    # end def

    def __del__(self):
        del self._input_device
        del self._output_device
        pygame.midi.quit()
    # end def

    @property
    def cb_event(self) -> Optional[Callable[[MidiEvent], None]]:
        return self._cb_event
    # end def

    @cb_event.setter
    def cb_event(self, value: Optional[Callable[[MidiEvent], None]]) -> None:
        self._cb_event = value
    # end def

    @staticmethod
    def _init_midi() -> None:
        # Set up pygame
        pygame.init()
        pygame.midi.init()
    # end def

    def play_note(self, note: int, velocity: int, channel: int = 0, instrument: Optional[int] = None, off: bool = False) -> None:
        if instrument is not None:
            # https://stackoverflow.com/questions/29805082/pygame-midi-multi-instrument
            self._output_device.set_instrument(instrument, channel)

        if not off:
            self._output_device.note_on(note, velocity, channel)
        else:
            self._output_device.note_off(note, velocity, channel)
        # end if
    # end def

    @staticmethod
    def get_midi_devices(device_type: Optional[MidiDeviceType] = None) -> List[MidiDeviceInfo]:
        Midi._init_midi()

        devices = list()

        for d, raw_device in enumerate(range(0, pygame.midi.get_count())):
            raw_device_info = pygame.midi.get_device_info(raw_device)
            device = MidiDeviceInfo(d,
                                    raw_device_info[0].decode(),
                                    raw_device_info[1].decode(),
                                    *raw_device_info[2:])
            if device_type is None or \
                    device_type == MidiDeviceType.INPUT and device.is_input or \
                    device_type == MidiDeviceType.OUTPUT and device.is_output:
                devices.append(device)
            # end if
        # end for

        return devices
    # end def

    def run(self) -> None:
        if self._input_device is not None:
            # Run the event loop
            while True:
                if self._input_device.poll():  # Spelling error in midi signature file
                    # No way to find number of messages in queue
                    events = self._input_device.read(1000)
                    for event in events:
                        if self._cb_event:
                            midi_event = MidiEvent(*event[0], event[1], self._midi_input_device_id)
                            self._cb_event(midi_event)
                        # end if
                    # end for

                    # Wait 10ms - this is arbitrary, but wait(0) still resulted in 100% cpu utilization
                pygame.time.wait(10)
            # end while
        # end def
    # end if
# end class
