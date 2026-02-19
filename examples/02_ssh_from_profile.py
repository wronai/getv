#!/usr/bin/env python3
"""SSH to any device using getv profiles — no more remembering IPs and passwords.

Setup once:
    getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PASSWORD=raspberry
    getv set devices nvidia SSH_HOST=192.168.1.50 SSH_USER=tom SSH_KEY_FILE=~/.ssh/id_rsa

Then connect:
    getv ssh rpi3                    # interactive shell
    getv ssh rpi3 "uname -a"        # run remote command

Or from Python:
"""

from getv.integrations.ssh import SSHEnv

# Load from profile
ssh = SSHEnv.from_profile("rpi3")

# Show connection info
print(f"Connecting to: {ssh.connection_string()}")
print(f"SSH command:   {' '.join(ssh.command())}")
print(f"Remote cmd:    {' '.join(ssh.command('uname -a'))}")

# SCP upload/download
print(f"SCP upload:    {' '.join(ssh.scp_to('local.txt', '/tmp/'))}")
print(f"SCP download:  {' '.join(ssh.scp_from('/tmp/remote.txt', './'))}")

# For paramiko (Python SSH library)
print(f"\nParamiko kwargs: {ssh.as_paramiko_kwargs()}")

# For fabric
print(f"Fabric kwargs:   {ssh.as_fabric_kwargs()}")

# Run a command (uncomment to actually execute):
# result = ssh.run("uname -a", capture=True)
# print(f"Output: {result.stdout}")
