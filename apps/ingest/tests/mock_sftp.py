"""
Starts and stops a mock SFTP server using the Python `sftpserver` module.
https://github.com/rspivak/sftpserver
"""
import os
import subprocess
import signal
import tempfile

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
            self.server = subprocess.Popen(
                server_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                start_new_session=True
            )

    def stop_server(self):
        """ Kill the process and remove the key file. """
        os.killpg(self.server.pid, signal.SIGTERM)
        os.remove(self.key_file)
        os.remove(f'{self.key_file}.pub')
