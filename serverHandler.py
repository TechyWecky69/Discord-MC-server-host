# server_handler.py
import subprocess
import threading
import queue
import functions
import os
import time
import asyncio


class ServerHandler:
    def __init__(self, SID: str, UID: str):
        """
        Handles a Minecraft server instance.
        :param SID: Server ID
        :param UID: User ID (owner)
        """
        self.SID = SID
        self.UID = UID
        self.process: subprocess.Popen = None
        self.line_queue = queue.Queue()
        self.running = False
        self.console_history = []
        self.max_history = 100

    def start(self):
        """
        Start the Minecraft server in the background.
        """
        owner_file = os.path.join("servers", self.SID, "owner.txt")
        if not os.path.exists(owner_file):
            raise FileNotFoundError(f"Owner file not found: {owner_file}")


#        with open(owner_file, "r") as f:
#            owner = f.read()
#        if self.UID != owner:
#            raise PermissionError("You are not the owner of this server.")

        server_dir = os.path.join("servers", self.SID)

        # RUN COMMAND => java -Xmx200m -Xms200m -jar server.jar --nogui

        self.process = subprocess.Popen(
            ["java", "-Xmx200m", "-Xms200m", "-jar", "server.jar", "--nogui"],
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.running = True

        threading.Thread(target=self._read_stdout, daemon=True).start()

    def _read_stdout(self):
        """
        Internal: reads server console output and stores in queue/history.
        """
        for line in self.process.stdout:
            line = line.strip()
            if line:
                self.line_queue.put(line)
                self.console_history.append(line)
                if len(self.console_history) > self.max_history:
                    self.console_history.pop(0)
                webhook_url = functions.get_webhook_url(self.UID, self.SID)
                if webhook_url:
                    try:
                        functions.send_webhook(webhook_url, line)
                    except Exception as e:
                        print(f"[Webhook Error] {e}")


    def command(self, command: str):
        """
        Sends a command to the Minecraft console.
        """
        if self.process and self.running:
            try:
                self.process.stdin.write(f"{command}\n")
                self.process.stdin.flush()
            except Exception as e:
                print(f"[Command Error] {e}")

    def stop(self):
        """
        Stops the server safely.
        """
        if self.process and self.running:
            try:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
                self.process.wait(timeout=30)
            except Exception as e:
                print(f"[Stop Error] {e}")
            finally:
                self.running = False

    def latest_line(self) -> str:
        """
        Returns the latest console line, non-blocking.
        """
        try:
            line = self.line_queue.get_nowait()
            return line
        except queue.Empty:
            return None

    def get_history(self, lines: int = 10):
        """
        Returns the last `lines` of console output.
        """
        return self.console_history[-lines:]