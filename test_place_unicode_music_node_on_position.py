import tkinter as tk

# Create the master object
master = tk.Tk()

# Create the label objects and pack them using grid
tk.Label(master, text="♫Label 123♫", font=("TkDefaultFont", 30, "normal")).grid(row=0, column=0)
lbl = tk.Label(master, text="♫", font=("TkDefaultFont", 50, "normal"))
# master.wm_attributes('-transparentcolor', master['bg'])
lbl.grid(row=0, column=0)

# Create the entry objects using master
e1 = tk.Entry(master)
e2 = tk.Entry(master)

# Pack them using grid
e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

# The mainloop
tk.mainloop()

# place elemente on pixel position
# https://stackoverflow.com/questions/44829601/set-the-pixel-location-of-a-button-in-tkinter

# music notes unicode
# https://www.alt-codes.net/music_note_alt_codes.php
