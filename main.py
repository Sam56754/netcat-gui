from tkinter import *
import subprocess
import psutil
import time
import socket

class NetcatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GS-Netcat Controller v1.3")
        self.root.geometry("500x400")
        
        # Variables
        self.mode = StringVar(value="")
        self.ip = StringVar(value="127.0.0.1")
        self.port = StringVar(value="12345")  # Changed from 22
        self.password = StringVar()
        self.process = None
        self.connection_socket = None #port cleanup
        
        self.show_mode_selection()

    def kill_existing_connections(self):
        """Kill any existing gs-netcat processes"""
        try:
            subprocess.run("pkill -f 'gs-netcat -l'", shell=True)
        except:
            pass

    def show_mode_selection(self):
        """First screen: Choose server or client mode"""
        self.clear_window()
        
        Label(self.root, text="Select Mode:", font=('Arial', 14)).pack(pady=20)
        
        Radiobutton(self.root, text="Server Mode", variable=self.mode, 
                   value="server", font=('Arial', 12)).pack(pady=5)
        Radiobutton(self.root, text="Client Mode", variable=self.mode, 
                   value="client", font=('Arial', 12)).pack(pady=5)
        
        Button(self.root, text="Continue", command=self.show_connection_settings,
              font=('Arial', 12)).pack(pady=20)

    def show_connection_settings(self):
        """Second screen: Show connection fields based on mode"""
        if not self.mode.get():
            return
            
        self.clear_window()
        
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
        """Execute the appropriate gs-netcat command with error handling"""
        self.force_release_port(self.port.get())
        self.kill_existing_connections()
        
        try:
            self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
            self.connection_socket.bind(('', int(self.port.get())))
        
            cmd = ""
            if self.mode.get() == "server":
                cmd = f"gs-netcat -l {self.ip.get()} {self.port.get()} -s {self.password.get()}"
            else:
                cmd = f"gs-netcat -l {self.port.get()} -s {self.password.get()}"
            
            self.process = subprocess.Popen(cmd, shell=True)
            self.show_connection_status(cmd)
            
        except socket.error:
            self.show_port_error()
        except Exception as e:
            self.show_error(str(e))

    def show_connection_status(self, cmd):
        """Show successful connection status"""
        self.clear_window()
        Label(self.root, text="✓ commands accepted", 
             font=('Arial', 14), fg="green").pack(pady=20)
        Label(self.root, text=f"Mode: {self.mode.get().title()}\nPort: {self.port.get()}").pack()
        
        console = Text(self.root, height=10, width=50)
        console.pack(pady=10, padx=10)
        console.insert(END, f"$ {cmd}\n")
        
        Button(self.root, text="Disconnect", command=self.disconnect,
              bg="red", fg="white").pack(pady=10)

    def show_port_error(self):
        """Show port in use error"""
        self.clear_window()
        Label(self.root, text="⚠ Port Error", font=('Arial', 14), fg="red").pack()
        Label(self.root, text=f"Port {self.port.get()} is already in use!\nPlease try a different port.").pack()
        Button(self.root, text="Try Again", command=self.show_connection_settings).pack()
        Button(self.root, text="Back to Menu", command=self.show_mode_selection).pack()

    def show_error(self, message):
        """Show general error"""
        self.clear_window()
        Label(self.root, text="Error", font=('Arial', 14), fg="red").pack()
        Label(self.root, text=message).pack()
        Button(self.root, text="Back", command=self.show_mode_selection).pack()
        
    def disconnect(self):
        """Clean up connection and release port"""
        # 1. Terminate the process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
        
        # 2. Close our port-holding socket
        if self.connection_socket:
            try:
                self.connection_socket.close()
            except:
                pass
        
        # 3. Additional cleanup for stubborn ports
        self.force_release_port(int(self.port.get()))
        
        self.show_mode_selection()

    def force_release_port(self, port):
        """Forcefully release a port by killing processes using it"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            proc.terminate()
                            proc.wait(timeout=1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Port cleanup warning: {str(e)}")
            
            
    def clear_window(self):
        """Remove all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()

# Run the application
root = Tk()
app = NetcatGUI(root)
root.mainloop()