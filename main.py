from tkinter import *
import subprocess

class NetcatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GS-Netcat Controller v1.2")
        self.root.geometry("400x300")
        
        # Variables
        self.mode = StringVar(value="")  # "server" or "client"
        self.ip = StringVar(value="127.0.0.1")  # Default IP
        self.port = StringVar(value="22")  # Default port
        self.password = StringVar()
        
        self.show_mode_selection()

    def show_mode_selection(self):
        """First screen: Choose server or client mode"""
        self.clear_window()
        
        Label(self.root, text="Select Mode:", font=('Arial', 14)).pack(pady=20)
        
        Frame(self.root).pack(pady=10)  # Spacer
        
        Radiobutton(self.root, text="Server Mode", variable=self.mode, 
                   value="server", font=('Arial', 12)).pack(pady=5)
        Radiobutton(self.root, text="Client Mode", variable=self.mode, 
                   value="client", font=('Arial', 12)).pack(pady=5)
        
        Frame(self.root).pack(pady=10)  # Spacer
        
        Button(self.root, text="Continue", command=self.show_connection_settings,
              font=('Arial', 12)).pack()

    def show_connection_settings(self):
        """Second screen: Show connection fields based on mode"""
        if not self.mode.get():
            return  # No mode selected
            
        self.clear_window()
        
        # Common fields
        Label(self.root, text=f"{self.mode.get().title()} Settings", 
             font=('Arial', 14)).pack(pady=10)
        
        if self.mode.get() == "server":
            Label(self.root, text="Server IP:").pack()
            Entry(self.root, textvariable=self.ip).pack()
        
        Label(self.root, text="Port:").pack()
        Entry(self.root, textvariable=self.port).pack()
        
        Label(self.root, text="Password:").pack()
        Entry(self.root, textvariable=self.password, show="*").pack()
        
        Button(self.root, text="START", command=self.start_connection,
              font=('Arial', 12), bg="green").pack(pady=20)
        
        Button(self.root, text="Back", command=self.show_mode_selection).pack()

    def start_connection(self):
        """Execute the appropriate gs-netcat command"""
        cmd = ""
        if self.mode.get() == "server":
            cmd = f"gs-netcat -l -d {self.ip.get()} -p {self.port.get()} -s {self.password.get()}"
        else:
            cmd = f"gs-netcat -p {self.port.get()} -s {self.password.get()}"
        
        print(f"Executing: {cmd}")  # For debugging
        subprocess.Popen(cmd, shell=True)
        
        # Show status
        self.clear_window()
        Label(self.root, text="Connection Running", font=('Arial', 14)).pack(pady=50)
        Label(self.root, text=f"Mode: {self.mode.get()}\nCommand: {cmd}").pack()
        Button(self.root, text="Back to Menu", command=self.show_mode_selection).pack()
        
    def messageDisplay(self):
        self.clear_window()
        

    def clear_window(self):
        """Remove all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()

# Run the application
root = Tk()
app = NetcatGUI(root)
root.mainloop()