from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, Text, Scrollbar
import socket
import threading
import sys

HOST = 'localhost'
PORT = 8000

s = None
balances = {
    "Davide": 100,
    "Giuseppe": 100,
    "Giovanni": 100,
    "Francesco": 100
}

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
    chat_display.insert(tk.END, f"Server: {data}\n")
    chat_display.yview(tk.END)

def on_fold():
    print("Fold")

def on_call():
    print("Call")

def on_raise():
    raise_amount = raise_slider.get()
    print(f"Raise by {raise_amount}")

def change_bg_color():
    new_color = color_entry.get()
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
    player_label.config(text=player_name)
    name_entry.grid_remove()
    save_button.grid_remove()
    ready_label.grid(row=0, column=0, columnspan=2)  # Display "Are you ready?" label
    yes_button.grid(row=0, column=2)  # Display "Yes" button

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

# Start Menu Widgets
name_entry = ttk.Entry(root, width=20)
name_entry.grid(row=0, column=0)
name_entry.insert(0, "Enter your name")

save_button = ttk.Button(root, text="Save", command=save_name)
save_button.grid(row=0, column=1)

ready_label = ttk.Label(root, text="Are you ready to start the game?")
yes_button = ttk.Button(root, text="Yes", command=start_game)

# Create frames
main_frame = tk.Frame(root, bg="white", padx=10, pady=10)
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
main_frame.grid_remove()  # Hide the main frame initially

# Label for Player name, Pot, and Balance
player_label = ttk.Label(main_frame, text="Davide")
player_label.grid(row=0, column=0, sticky=tk.W)

pot_label = ttk.Label(main_frame, text="Pot: 100")
pot_label.grid(row=0, column=2, sticky=tk.EW)

balance_label = ttk.Label(main_frame, text="Balances:")
for idx, (name, balance) in enumerate(balances.items()):
    balance_label["text"] += f"\n{name}: {balance}"
balance_label.grid(row=0, column=4, sticky=tk.E)

def update_ui(balances):
    balance_label["text"] = "Balances:"
    for idx, (name, balance) in enumerate(balances.items()):
        balance_label["text"] += f"\n{name}: {balance}"

# Load and resize Card Image
original_img = Image.open("img/background.png")
width, height = original_img.size
new_img = original_img.resize((width // 5, height // 5), Image.ANTIALIAS)
card_img = ImageTk.PhotoImage(new_img)

# Display 5 community cards
community_cards = [ttk.Label(main_frame, image=card_img) for _ in range(5)]
for idx, lbl in enumerate(community_cards):
    lbl.grid(row=1, column=idx)

# Display 2 hole cards
hole_cards = [ttk.Label(main_frame, image=card_img) for _ in range(2)]
for idx, lbl in enumerate(hole_cards):
    lbl.grid(row=2, column=idx, columnspan=2)

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
action_buttons = [call_button, raise_button, fold_button]

def toggle_visibility():
    new_state = 'normal' if fold_button.winfo_viewable() == 0 else 'hidden'
    for widget in input_bar_widgets + action_buttons:
        if new_state == 'hidden':
            widget.grid_remove()
        else:
            widget.grid()

# Button to toggle visibility
toggle_button = ttk.Button(root, text="Toggle Visibility", command=toggle_visibility)
toggle_button.grid(row=1, column=0, sticky=tk.W)

# Button to change background color and a text field for the color
color_entry = ttk.Entry(main_frame, width=10)
color_entry.grid(row=6, column=0, sticky=(tk.W, tk.E))
color_entry.insert(0, "white")
change_color_button = ttk.Button(main_frame, text="Change BG Color", command=change_bg_color)
change_color_button.grid(row=6, column=1, sticky=tk.W)

## End of GUI

if __name__ == "__main__":
    # Start socket client
    threading.Thread(target=socket_client).start()

    # Run the Tkinter event loop
    root.mainloop()