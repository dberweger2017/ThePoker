from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, Text, Scrollbar
import socket
import threading
import sys
import names
import os

HOST = 'localhost'
PORT = 8000

s = None
player_name = None
balances = {}
cards_on_table = [10, 13, 12]
cards_for_player = []

def get_mode():
    return "admin" if sys.argv[1:2] == ["admin"] else "client"

def socket_client():
    global s

    mode = get_mode()
    print(f"{mode.capitalize()} mode")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.send(mode.encode())
        while True:
            data = s.recv(1024)
            if data:
                handle_data(s, data.decode())
    except ConnectionRefusedError:
        print("The server is not running.")
        chat_display.insert(tk.END, "The server is not running.\n")
    except ConnectionResetError:
        print("The server has closed the connection.")
        chat_display.insert(tk.END, "The server has closed the connection.\n")

def handle_data(s, data):
    global player_name
    decoded_data = data.strip().split("\n")
    for line in decoded_data:
        if line == " "*len(line):
            continue
        if line.startswith("(D)") or line.startswith(" (D)"):
            # Server is requesting data, send it quitely in the background
            if line == "(D)-name":
                s.send(player_name.encode())
            else:
                print(f"Unknown data request: {line}")
        elif line.startswith("(I)") or line.startswith(" (I)"):
            # The server is showing information, display it to the user
            line = line.replace("(I)", "").strip()
            chat_display.insert(tk.END, f"Server: {data}\n")
            chat_display.yview(tk.END)
        elif line.startswith("(C)") or line.startswith(" (C)"):
            # The server is requesting input from the user
            line = line.replace("(C)", "").strip()
            # For now, just show the information to the user
            chat_display.insert(tk.END, f"Server: {data}\n")
            chat_display.yview(tk.END)

def on_fold():
    print("Fold")

def on_call():
    print("Call")

def on_raise():
    raise_amount = raise_slider.get()
    print(f"Raise by {raise_amount}")

def change_bg_color(new_color):
    main_frame.config(bg=new_color)

def send_message():
    global s
    message = chat_input.get()
    chat_display.insert(tk.END, f"You: {message}\n")
    chat_input.delete(0, tk.END)
    chat_display.yview(tk.END)
    if s:
        try:
            s.send(message.encode())
        except:
            chat_display.insert(tk.END, "Failed to send message. Connection might be closed.\n")

## GUI

def save_name():
    global player_name
    player_name = name_entry.get()
    threading.Thread(target=socket_client).start()
    player_label.config(text=player_name)
    name_label.grid_remove()
    name_entry.grid_remove()
    save_button.grid_remove()
    ready_label.grid(row=0, column=0, columnspan=2)
    yes_button.grid(row=0, column=2)

def start_game():
    global s
    s.send("y".encode())
    ready_label.grid_remove()
    yes_button.grid_remove()
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))  # Show the main frame

# Initialize Tkinter window
root = tk.Tk()
root.title("Poker Game")
root.geometry("600x680")

# Enter your name
name_label = ttk.Label(root, text="Enter your name:")
name_label.grid(row=0, column=0, sticky=tk.W)

name_entry = ttk.Entry(root, width=20)
name_entry.grid(row=1, column=0)
name_entry.insert(0, f"{names.get_first_name()}")

save_button = ttk.Button(root, text="Save", command=save_name)
save_button.grid(row=0, column=1)

ready_label = ttk.Label(root, text="Are you ready to start the game?")
yes_button = ttk.Button(root, text="Yes", command=start_game)

# Create frames
main_frame = tk.Frame(root, bg="white", padx=10, pady=10)
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
main_frame.grid_remove()

# Label for Player name, Pot, and Balance
player_label = ttk.Label(main_frame, text=player_name)
player_label.grid(row=0, column=0, sticky=tk.W)

pot_label = ttk.Label(main_frame, text="Pot: 100")
pot_label.grid(row=0, column=2, sticky=tk.EW)

balance_label = ttk.Label(main_frame, text="Balances:")
for idx, (name, balance) in enumerate(balances.items()):
    balance_label["text"] += f"\n{name}: {balance}"
balance_label.grid(row=0, column=4, sticky=tk.E)

def update_balances(balances):
    balance_label["text"] = "Balances:"
    for idx, (name, balance) in enumerate(balances.items()):
        balance_label["text"] += f"\n{name}: {balance}"

def update_cards(cards, row, starting_column=0):
        for idx, card in enumerate(cards):
            card_img_path = f"img/{card}.png"
            if not os.path.exists(card_img_path):
                print(f"Card image {card_img_path} not found!")
                continue
            original_card_img = Image.open(card_img_path)
            card_img = ImageTk.PhotoImage(original_card_img.resize((width // 5, height // 5), Image.ANTIALIAS))
            card_label = ttk.Label(main_frame, image=card_img)
            card_label.image = card_img  # Keep a reference
            card_label.grid(row=row, column=starting_column + idx)

def update_ui():
    global balances, cards_on_table, cards_for_player
    update_balances(balances)
    update_cards(cards_on_table, 1)
    update_cards(cards_for_player, 2)

# Chat display
chat_display = Text(main_frame, wrap=tk.WORD, width=50, height=10)
chat_display.grid(row=3, column=0, columnspan=5, pady=5, sticky=(tk.W, tk.E))

# Adding Scrollbar
scrollbar = Scrollbar(main_frame, orient="vertical", command=chat_display.yview)
scrollbar.grid(row=3, column=5, sticky=(tk.N, tk.S))
chat_display.config(yscrollcommand=scrollbar.set)

# Poker Action Buttons and Slider
fold_button = ttk.Button(main_frame, text="Fold", command=on_fold)
fold_button.grid(row=4, column=0)

call_button = ttk.Button(main_frame, text="Call", command=on_call)
call_button.grid(row=4, column=1)

raise_button = ttk.Button(main_frame, text="Raise", command=on_raise)
raise_button.grid(row=4, column=2)

raise_slider = tk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                        sliderlength=30, width=20, troughcolor='grey',
                        background='lightgrey')
raise_slider.grid(row=4, column=3)
raise_slider.set(50)

# Chat Input and Send button
chat_input = ttk.Entry(main_frame, width=30)
chat_input.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
send_button = ttk.Button(main_frame, text="Send", command=send_message)
send_button.grid(row=5, column=3, sticky=tk.W)

# Group widgets by their function
input_bar_widgets = [chat_input, send_button]
action_buttons = [call_button, raise_button, raise_slider, fold_button]

def toggle_visibility():
    new_state = 'normal' if fold_button.winfo_viewable() == 0 else 'hidden'
    for widget in input_bar_widgets + action_buttons:
        if new_state == 'hidden':
            widget.grid_remove()
        else:
            widget.grid()

# Button to change background color and a text field for the color
change_color_button = ttk.Button(main_frame, text="Change BG Color", command=change_bg_color)
change_color_button.grid(row=6, column=1, sticky=tk.W)

## End of GUI

# update_ui() every 100ms to update the UI
root.after(100, update_ui)
root.mainloop()