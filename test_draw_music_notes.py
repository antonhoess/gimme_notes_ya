import os
import music21 as m21


def get_note():
    n = m21.note.Note("D#3")
    n.duration.type = "half"

    return n


def get_stream():
    s = m21.stream.Stream()
    s.append(m21.key.Key("E-"))
    s.append(m21.meter.TimeSignature("2/4"))
    s.append(m21.note.Rest(quarterLength=0.5))
    s.append(m21.note.Note("g", quarterLength=0.5))
    s.append(m21.note.Note("g", quarterLength=0.5))
    s.append(m21.note.Note("g", quarterLength=0.5))
    s.append(m21.note.Note("e-", quarterLength=2))

    return s


def main():
    # Paths
    muse_score = r"MuseScore3.exe"  # needs musescore bin-directory to be in the PATH environment variable
    file_base_path = os.path.dirname(os.path.abspath(__file__))
    musicxml_file_subpath = r"notes\Die Super-Riesen-Schlingel-Schlange.musicxml"

    # Convert musicxml file to PNG score
    cmd = f"{muse_score} \"{os.path.join(file_base_path, musicxml_file_subpath)}\" -o \"{os.path.join(file_base_path, os.path.splitext(musicxml_file_subpath)[0] + '.png')}\""
    print(cmd)
    os.system(cmd)

    # Create score from scratch
    x = get_stream()  # or get_note() as another example

    # Show note - opens muse score showing that note/score
    x.show()

    # Makes problems because of the space in "C:\Program Files\..."
    # -> a possible solution might have to do with "m21.environment.UserSettings()" or "m21.environment.Environment()"
    # -> us["musescoreDirectPNGPath"] and us["musicxmlPath"]
    x.show("musicxml.png")


if __name__ == "__main__":
    main()
