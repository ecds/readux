"""
Starts and stops a mock SFTP server using the Python `sftpserver` module.
https://github.com/rspivak/sftpserver
"""
import os
import signal
import socket
import subprocess
import tempfile
import logging

LOGGER = logging.getLogger(__name__)


class MockSFTP:
    """
    The `sftpserver` module does not provide an obvious way to start a server, do
    some stuff, and then stop the server. There is a plugin for PyTest, but it
    seems to create a read-only server. I don't love this, but it will work for now.
    :(
    """
    def __init__(self):
        self.key_file = os.path.join(tempfile.gettempdir(), 'readux_test_sshkey')
        self.port = 3373
        self.host = 'localhost'
        self.server = None

        if not os.path.exists(self.key_file):
            subprocess.run(f'ssh-keygen -b 2048 -t rsa -f {self.key_file} -q -N ""', shell=True, check=True)

        server_command = f'sftpserver -k {self.key_file} -p {self.port} --host {self.host}'

        if not self.server:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, self.port))
                sock.close()
                self.server = subprocess.Popen(
                    server_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    start_new_session=True
                )
            except OSError:
                # For CircleCI, the sftp server is started in the background.
                pass

    def stop_server(self):
        """ Kill the process and remove the key file. """
        if self.server:
            try:
                os.killpg(self.server.pid, signal.SIGTERM)
                os.remove(self.key_file)
                os.remove(f'{self.key_file}.pub')
            except PermissionError:
                LOGGER.error(f'Failed to kill mock SFTP server with pit {self.server.pid}')