from tkinter import *
from connection import NetcatConnection
import queue
import threading

class NetcatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GS-Netcat Controller v3.0 with encapsulated")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        # Variables
        self.mode = StringVar(value="")
        self.password = StringVar()
        self.process = None
        self.connection_socket = None
        
        # Chat UI elements
        self.chat_canvas = None
        self.chat_frame = None
        self.chat_scrollbar = None
        self.msg_entry = None
        self.send_button = None
        
        self.stdout_queue = queue.Queue()
        self.read_thread = None
        self.reading = False
        
        # Connection handler
        self.connection = NetcatConnection()
        
        # Initialize UI
        self.show_mode_selection()

    def show_mode_selection(self):
        """Show the initial mode selection screen"""
        self.clear_window()
        
        # Title
        Label(self.root, text="Select Mode:", font=('Arial', 14)).pack(pady=20)
        
        # Mode selection radio buttons
        Radiobutton(
            self.root, 
            text="Server Mode", 
            variable=self.mode, 
            value="server", 
            font=('Arial', 12)
        ).pack(pady=5)
        
        Radiobutton(
            self.root, 
            text="Client Mode", 
            variable=self.mode, 
            value="client", 
            font=('Arial', 12)
        ).pack(pady=5)
        
        # Continue button
        Button(
            self.root, 
            text="Continue", 
            command=self.show_connection_settings,
            font=('Arial', 12)
        ).pack(pady=20)

    def show_connection_settings(self):
        """Show connection settings screen"""
        if not self.mode.get():
            return
            
        self.clear_window()
        
        # Title
        Label(
            self.root, 
            text=f"{self.mode.get().title()} Settings", 
            font=('Arial', 14)
        ).pack(pady=10)
        
        # Password entry
        Label(self.root, text="Password:").pack()
        Entry(
            self.root, 
            textvariable=self.password, 
            font=('Arial', 12)
        ).pack()
        
        # Start button
        self.start_button = Button(
            self.root, 
            text="START", 
            command=self.start_connection,
            font=('Arial', 12), 
            bg="green",
            fg="white"
        )
        self.start_button.pack(pady=30)
        
        # Bind Enter key to start connection
        self.root.bind('<Return>', lambda event: self.start_connection())
        
        # Back button
        Button(
            self.root, 
            text="Back", 
            command=self.show_mode_selection,
            font=('Arial', 10)
        ).pack()

    def show_connection_status(self, cmd):
        """Show the complete connection interface with chat"""
        self.clear_window()
        
        # Connection status header
        Label(self.root, 
              text="✓ Connection Established",
              font=('Arial', 14, 'bold'),
              fg="green").pack(pady=5)
        
        # Mode display
        mode_frame = Frame(self.root)
        mode_frame.pack()
        Label(mode_frame, 
              text="Mode:", 
              font=('Arial', 10, 'bold')).pack(side=LEFT)
        Label(mode_frame, 
              text=f"{self.mode.get().title()}",
              font=('Arial', 10)).pack(side=LEFT, padx=5)

        # Security info box
        security_frame = Frame(self.root, bd=1, relief="solid", padx=10, pady=5, bg="#f5f5f5")
        security_frame.pack(pady=10, fill=X, padx=20)
        
        # Password display
        Label(security_frame,
              text=f"Access Password: {'*' * len(self.password.get())}",
              font=('Arial', 10),
              bg="#f5f5f5").pack(anchor="w")
        
        # Encryption display
        Label(security_frame,
              text="welcome to generic chat app 101",
              font=('Arial', 10),
              bg="#f5f5f5").pack(anchor="w")

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

        # Input area
        input_frame = Frame(self.root)
        input_frame.pack(padx=10, pady=5, fill=X)

        self.msg_entry = Entry(input_frame, font=('Arial', 12))
        self.msg_entry.pack(side=LEFT, fill=X, expand=True, padx=(0,5))
        self.msg_entry.bind("<Return>", self.send_message)
        
        self.send_button = Button(input_frame, 
                                text="Send", 
                                command=self.send_message,
                                bg="#25d366", 
                                fg="white", 
                                font=('Arial', 11))
        self.send_button.pack(side=RIGHT)

        # Disconnect button
        Button(self.root, 
              text="Disconnect", 
              command=self.disconnect,
              bg="red", 
              fg="white", 
              font=('Arial', 12)).pack(pady=5)

        # Hidden command logging
        self.add_chat_message("system", f"$ {cmd}", show=False)
        
    def add_chat_message(self, sender, message, show=True):
        """Add a message bubble to the chat"""
        if not show:
            return 
        
        if not hasattr(self, 'chat_frame') or not self.chat_frame:
            return

        msg_frame = Frame(self.chat_frame, bg="#e5ddd5", pady=2)
        msg_frame.pack(fill=X, pady=1)

        # Configure bubble appearance based on sender
        if sender == "peer":
            bubble_color = "white"
            anchor_side = "w"  # Left alignment
            padx_val = 0
            justify = "left"
        elif sender == "system":
            bubble_color = "#f0f0f0"
            anchor_side = "center"  # Center alignment
            padx_val = 0
            justify = "center"
        else:  # "you"
            bubble_color = "#dcf8c6"
            anchor_side = "e"  # Right alignment
            padx_val = 10
            justify = "right"

        # Create the message bubble
        bubble = Label(
            msg_frame,
            text=message,
            bg=bubble_color,
            fg="black",
            font=('Arial', 11),
            wraplength=280,
            justify=justify,
            bd=1,
            relief="solid",
            padx=8,
            pady=5
        )
        
        # Use proper packing based on alignment
        if sender == "system":
            bubble.pack(anchor="center", padx=padx_val)
        elif sender == "peer":
            bubble.pack(anchor="w", padx=padx_val)
        else:  # "you"
            bubble.pack(anchor="e", padx=padx_val)

        # Auto-scroll to bottom
        self._safe_scroll_to_bottom()

    def _safe_scroll_to_bottom(self):
        """Safely handle scrolling to avoid TclError"""
        if hasattr(self, 'chat_canvas') and self.chat_canvas:
            try:
                self.chat_canvas.yview_moveto(1.0)
            except:
                pass

    def show_error(self, message):
        """Show error message screen"""
        self.clear_window()
        Label(
            self.root, 
            text="Error", 
            font=('Arial', 14), 
            fg="red"
        ).pack(pady=10)
        
        Label(
            self.root, 
            text=message, 
            font=('Arial', 11)
        ).pack(pady=5)
        
        Button(
            self.root, 
            text="Back", 
            command=self.show_mode_selection,
            font=('Arial', 11)
        ).pack(pady=5)
        
    def start_connection(self):
        def message_callback(sender, msg):
            self.add_chat_message(sender, msg)
        
        success, result = self.connection.start_connection(
            mode=self.mode.get(),
            password=self.password.get(),
            callback=message_callback
        )
        
        if success:
            self.show_connection_status(result)
        else:
            self.show_error(f"Connection failed: {result}")

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
            
    def send_message(self, event=None):
        msg = self.msg_entry.get().strip()
        if msg:
            try:
                self.connection.send_message(msg)
                self.add_chat_message("you", msg)
                self.msg_entry.delete(0, END)
            except Exception as e:
                self.add_chat_message("system", f"[ERROR] {str(e)}")
        return "break"

    def disconnect(self):
        """Clean up connection and reset UI"""
        # Clear connection first
        self.connection.disconnect()
        self.process = None
        self.connection_socket = None
        
        # Clear chat-related widgets safely
        if hasattr(self, 'chat_canvas'):
            try:
                self.chat_canvas.destroy()
            except:
                pass
        if hasattr(self, 'chat_frame'):
            try:
                self.chat_frame.destroy()
            except:
                pass
        
        # Reset chat UI references
        self.chat_canvas = None
        self.chat_frame = None
        self.chat_scrollbar = None
        self.msg_entry = None
        self.send_button = None
        
        # Clear any queued messages
        self.stdout_queue.queue.clear()
        
        # Return to mode selection
        self.show_mode_selection()
