#!/usr/bin/env python3
"""Generate Docker env files and compose fragments from getv profiles.

Setup:
    getv set llm groq LLM_MODEL=groq/llama-3.3-70b-versatile GROQ_API_KEY=gsk_xxx
    getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi

Usage:
    # Write Docker env file
    getv export llm groq --format docker > /tmp/docker.env
    docker run --env-file /tmp/docker.env my-image

    # Or from Python:
"""

from getv.integrations.docker import DockerEnv

# --- Single profile ---

try:
    denv = DockerEnv.from_profile("llm", "groq")

    # Docker --env-file content
    print("=== Docker env file ===")
    for k, v in sorted(denv.as_dict().items()):
        print(f"{k}={v}")

    # Docker run command
    print(f"\n=== Docker run ===")
    cmd = denv.run_command("my-llm-app:latest", "python main.py")
    print(" ".join(cmd))

    # Docker compose environment block
    print(f"\n=== Docker compose ===")
    print(denv.compose_environment())

except FileNotFoundError:
    print("No 'groq' LLM profile. Create: getv set llm groq LLM_MODEL=groq/llama3 GROQ_API_KEY=gsk_xxx")

# --- Merge multiple profiles ---

try:
    merged = DockerEnv.from_profiles(llm="groq", devices="rpi3")
    print(f"\n=== Merged env (llm+devices) ===")
    for k, v in sorted(merged.as_dict().items()):
        print(f"  {k}={v}")
except FileNotFoundError as e:
    print(f"\nMerge skipped: {e}")
