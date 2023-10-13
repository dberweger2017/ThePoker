from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, Text, Scrollbar
import socket
import threading

HOST = 'localhost'
PORT = 8000

def socket_client():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        while True:
            data = s.recv(1024)
            if data:
                handle_data(s, data.decode())
    except ConnectionRefusedError:
        print("The server is not running.")
    except ConnectionResetError:
        print("The server has closed the connection.")

def handle_data(s, data):
    chat_display.insert(tk.END, f"Server: {data}\n")
    chat_display.yview(tk.END)  # Scroll to the end

# Poker Action functions
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

def toggle_visibility():
    new_state = 'normal' if fold_button.winfo_viewable() == 0 else 'hidden'
    for widget in main_frame.winfo_children():
        if widget not in community_cards and widget not in hole_cards and widget != chat_display:
            widget.grid_remove() if new_state == 'hidden' else widget.grid()

def send_message():
    message = chat_input.get()
    chat_display.insert(tk.END, f"You: {message}\n")
    chat_input.delete(0, tk.END)
    chat_display.yview(tk.END)

# Initialize Tkinter window
root = tk.Tk()
root.title("Poker Game")

# Create frames
main_frame = tk.Frame(root, bg="white", padx=10, pady=10)
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Label for Player name, Pot, and Balance
player_label = ttk.Label(main_frame, text="Davide")
player_label.grid(row=0, column=0, sticky=tk.W)

pot_label = ttk.Label(main_frame, text="Pot: 100")
pot_label.grid(row=0, column=2, sticky=tk.EW)

balance_label = ttk.Label(main_frame, text="Balance: 1000")
balance_label.grid(row=0, column=4, sticky=tk.E)

# Button to toggle visibility
toggle_button = ttk.Button(root, text="Toggle Visibility", command=toggle_visibility)
toggle_button.grid(row=1, column=0, sticky=tk.W)

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

# Button to change background color and a text field for the color
color_entry = ttk.Entry(main_frame, width=10)
color_entry.grid(row=6, column=0, sticky=(tk.W, tk.E))
color_entry.insert(0, "white")
change_color_button = ttk.Button(main_frame, text="Change BG Color", command=change_bg_color)
change_color_button.grid(row=6, column=1, sticky=tk.W)

# Start socket client
threading.Thread(target=socket_client).start()

# Run the Tkinter event loop
root.mainloop()