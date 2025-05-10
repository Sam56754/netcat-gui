from tkinter import *
import time
import subprocess
import socket
import threading
import queue


class NetcatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GS-Netcat Controller v2.1 with Chat Bubbles")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        # Variables
        self.mode = StringVar(value="")
        self.password = StringVar()
        self.process = None
        self.connection_socket = None
        
        # Chat UI elements placeholders
        self.chat_canvas = None
        self.chat_frame = None
        self.chat_scrollbar = None
        self.msg_entry = None 
        self.send_button = None
        
        self.stdout_queue = queue.Queue()
        self.read_thread = None
        self.reading = False
        
        self.show_mode_selection()

    def kill_existing_connections(self):
        """Kill any existing gs-netcat processes"""
        try:
            subprocess.run("pkill -f 'gs-netcat -l'", shell=True)
        except:
            pass

    def show_mode_selection(self):
        self.clear_window()
        
        Label(self.root, text="Select Mode:", font=('Arial', 14)).pack(pady=20)
        
        Radiobutton(self.root, text="Server Mode", variable=self.mode, 
                   value="server", font=('Arial', 12)).pack(pady=5)
        Radiobutton(self.root, text="Client Mode", variable=self.mode, 
                   value="client", font=('Arial', 12)).pack(pady=5)
        
        Button(self.root, text="Continue", command=self.show_connection_settings,
              font=('Arial', 12)).pack(pady=20)
        
    def show_connection_settings(self):
        if not self.mode.get():
            return
        
        self.clear_window()
    
        Label(self.root, text=f"{self.mode.get().title()} Settings", 
             font=('Arial', 14)).pack(pady=10)
    

        Label(self.root, text="Password:").pack()
        Entry(self.root, textvariable=self.password, show="*").pack()
    
        # Create the START button as a variable so we can bind Enter to its command
        self.start_button = Button(self.root, text="START", command=self.start_connection,
                  font=('Arial', 12), bg="green")
        self.start_button.pack(pady=30)

        # Bind the Enter key to call start_connection when pressed anywhere in this window
        self.root.bind('<Return>', lambda event: self.start_connection())
    
        Button(self.root, text="Back", command=self.show_mode_selection).pack()
        
    def start_connection(self):
        self.kill_existing_connections()

        retries = 100
        delay = 2  # seconds

        for attempt in range(1, retries + 1):
            try:
                self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                cmd_args = []
                if self.mode.get() == "server":
                    cmd_args = ["gs-netcat", "-l", "-s", self.password.get()]
                else:
                    cmd_args = ["gs-netcat", "-s", self.password.get()]
                    # NOTE: If you plan to add a custom IP field later, you'd add it here

                self.process = subprocess.Popen(
                    cmd_args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                self.show_connection_status(" ".join(cmd_args))

                self.reading = True
                self.read_thread = threading.Thread(target=self._read_output, daemon=True)
                self.read_thread.start()

                return  # success, exit function

            except Exception as e:
                self.clear_window()
                Label(self.root, text="Connection Failed", font=('Arial', 14), fg="red").pack(pady=10)
                Label(self.root, text=f"Attempt {attempt} of {retries}").pack(pady=5)
                self.root.update()
                time.sleep(delay)

            # If we reach here, all attempts failed
            self.show_error("All connection attempts failed.")


    def show_connection_status(self, cmd):
        self.clear_window()

        Label(self.root, text="✓ Connection established", 
             font=('Arial', 14), fg="green").pack(pady=6)
        Label(self.root, text=f"Mode: {self.mode.get().title()}", font=('Arial', 10)).pack(pady=4)

        # Chat area setup - scrollable canvas with frame
        chat_container = Frame(self.root)
        chat_container.pack(padx=10, pady=5, fill=BOTH, expand=True)

        self.chat_canvas = Canvas(chat_container, bg="#e5ddd5", height=350, width=480, highlightthickness=0)
        self.chat_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.chat_scrollbar = Scrollbar(chat_container, orient=VERTICAL, command=self.chat_canvas.yview)
        self.chat_scrollbar.pack(side=RIGHT, fill=Y)

        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_frame = Frame(self.chat_canvas, bg="#e5ddd5")
        self.chat_canvas.create_window((0,0), window=self.chat_frame, anchor="nw", width=460)

        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))

        # Initial command message
        self.add_chat_message("system", f"$ {cmd}")

        input_frame = Frame(self.root)
        input_frame.pack(padx=10, pady=5, fill=X)

        self.msg_entry = Entry(input_frame, font=('Arial', 12))
        self.msg_entry.pack(side=LEFT, fill=X, expand=True, padx=(0,5))
        self.msg_entry.bind("<Return>", self.send_message)
        

        self.send_button = Button(input_frame, text="Send", command=self.send_message, bg="#25d366", fg="white", font=('Arial', 11))
        self.send_button.pack(side=RIGHT)

        Button(self.root, text="Disconnect", command=self.disconnect,
              bg="red", fg="white", font=('Arial', 12)).pack(pady=10)

    def add_chat_message(self, sender, message):
        # Create a message bubble aligned left or right with colors
        # sender: "you", "peer", or "system"
        msg_frame = Frame(self.chat_frame, bg="#e5ddd5", pady=2)
        msg_frame.pack(fill=X, pady=1)

        bubble_color = "#dcf8c6"  # default "you" bubble (light green)
        text_color = "black"
        anchor_side = E
        padx_val = 10
        if sender == "peer":
            bubble_color = "white"
            anchor_side = W
            padx_val = 0
        elif sender == "system":
            bubble_color = "#f0f0f0"
            anchor_side = CENTER
            padx_val = 0

        bubble = Label(
            msg_frame,
            text=message,
            bg=bubble_color,
            fg=text_color,
            font=('Arial', 11),
            wraplength=280,
            justify=LEFT if sender == "peer" else RIGHT,
            bd=1,
            relief="solid",
            padx=8,
            pady=5
        )

        bubble.pack(anchor=anchor_side, padx=padx_val)

        # After adding a message, auto scroll to bottom
        self.root.after(100, lambda: self.chat_canvas.yview_moveto(1.0))

    def send_message(self, event=None):
        if not self.process or self.process.stdin.closed:
            self.add_chat_message("system", "[ERROR] Connection closed, unable to send message.")
            return "break"

        msg = self.msg_entry.get().strip()
        if msg == "":
            return "break"  # ignore empty messages

        try:
            self.process.stdin.write(msg + "\n")
            self.process.stdin.flush()

            self.add_chat_message("you", msg)
            self.msg_entry.delete(0, END)

        except Exception as e:
            self.add_chat_message("system", f"[ERROR] Failed to send message: {e}")

        return "break"

    def _read_output(self):
        try:
            while self.reading and self.process and not self.process.stdout.closed:
                line = self.process.stdout.readline()
                if line == "":
                    break
                self.stdout_queue.put(line.strip())
                self.root.after(100, self._update_chat_from_queue)
        except Exception as e:
            self.stdout_queue.put(f"[ERROR] Failed to read from connection: {e}")
            self.root.after(100, self._update_chat_from_queue)

    def _update_chat_from_queue(self):
        while not self.stdout_queue.empty():
            try:
                msg = self.stdout_queue.get_nowait()
                if msg:
                    self.add_chat_message("peer", msg)
            except queue.Empty:
                break

    def show_error(self, message):
        self.clear_window()
        Label(self.root, text="Error", font=('Arial', 14), fg="red").pack(pady=10)
        Label(self.root, text=message).pack(pady=5)
        Button(self.root, text="Back", command=self.show_mode_selection).pack(pady=5)

    def disconnect(self):
        self.reading = False
        
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        
        if self.connection_socket:
            try:
                self.connection_socket.close()
            except:
                pass
            self.connection_socket = None
        
        
        self.stdout_queue.queue.clear()
        self.show_mode_selection()

                
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = Tk()
    app = NetcatGUI(root)
    root.mainloop()
