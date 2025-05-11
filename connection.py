import subprocess
import socket
import threading
import time

class NetcatConnection:
    def __init__(self):
        self.process = None
        self.connection_socket = None
        self.reading = False
        self.retries = 100
        self.delay = 2  # seconds

    def kill_existing_connections(self):
        try:
            subprocess.run("pkill -f 'gs-netcat -l'", shell=True)
        except:
            pass

    def start_connection(self, mode, password, callback=None):
        self.kill_existing_connections()
        for attempt in range(1, self.retries + 1):
            try:
                self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                cmd_args = ["gs-netcat", "-s", password]
                if mode == "server":
                    cmd_args.insert(1, "-l")

                self.process = subprocess.Popen(
                    cmd_args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                if callback:
                    self.reading = True
                    threading.Thread(
                        target=self.read_output,
                        args=(callback,),
                        daemon=True
                    ).start()

                return True, " ".join(cmd_args)
            except Exception as e:
                if attempt == self.retries:
                    return False, str(e)
                time.sleep(self.delay)

    def read_output(self, callback):
        try:
            while self.reading and self.process and not self.process.stdout.closed:
                line = self.process.stdout.readline()
                if line == "":
                    break
                callback("peer", line.strip())
        except Exception as e:
            callback("system", f"[ERROR] {str(e)}")

    def send_message(self, message):
        if not self.process or self.process.stdin.closed:
            raise ConnectionError("Connection closed")
        if message.strip():
            self.process.stdin.write(message + "\n")
            self.process.stdin.flush()

    def disconnect(self):
        self.reading = False
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        if self.connection_socket:
            try:
                self.connection_socket.close()
            except:
                pass