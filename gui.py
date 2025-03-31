import argparse
import locale
import os
import platform
import subprocess
import sys
import asyncio
import gradio as gr

# Colab-specific imports
try:
    from pyngrok import ngrok
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
    from pyngrok import ngrok

from mikazuki.launch_utils import (base_dir_path, catch_exception, git_tag,
                                   prepare_environment, check_port_avaliable, find_avaliable_ports)
from mikazuki.log import log

parser = argparse.ArgumentParser(description="GUI for stable diffusion training")
parser.add_argument("--host", type=str, default="0.0.0.0")  # Changed default to 0.0.0.0 for Colab
parser.add_argument("--port", type=int, default=28000, help="Port to run the server on")
parser.add_argument("--listen", action="store_true")
parser.add_argument("--skip-prepare-environment", action="store_true")
parser.add_argument("--skip-prepare-onnxruntime", action="store_true")
parser.add_argument("--disable-tensorboard", action="store_true")
parser.add_argument("--disable-tageditor", action="store_true")
parser.add_argument("--disable-auto-mirror", action="store_true")
parser.add_argument("--tensorboard-host", type=str, default="0.0.0.0", help="Port to run the tensorboard")
parser.add_argument("--tensorboard-port", type=int, default=6006, help="Port to run the tensorboard")
parser.add_argument("--localization", type=str)
parser.add_argument("--dev", action="store_true")
parser.add_argument("--ngrok-token", type=str, help="Your ngrok authtoken for public URL")

@catch_exception
def run_tensorboard():
    log.info("Starting tensorboard...")
    subprocess.Popen([sys.executable, "-m", "tensorboard.main", "--logdir", "logs",
                     "--host", args.tensorboard_host, "--port", str(args.tensorboard_port)])

@catch_exception
def run_tag_editor():
    log.info("Starting tageditor...")
    cmd = [
        sys.executable,
        base_dir_path() / "mikazuki/dataset-tag-editor/scripts/launch.py",
        "--port", "28001",
        "--shadow-gradio-output",
        "--root-path", "/proxy/tageditor"
    ]
    if args.localization:
        cmd.extend(["--localization", args.localization])
    else:
        l = locale.getdefaultlocale()[0]
        if l and l.startswith("zh"):
            cmd.extend(["--localization", "zh-Hans"])
    subprocess.Popen(cmd)

def setup_ngrok(port):
    if not args.ngrok_token:
        log.error("Please provide an ngrok token using --ngrok-token. Get it from https://dashboard.ngrok.com/")
        sys.exit(1)
    ngrok.set_auth_token(args.ngrok_token)
    public_url = ngrok.connect(port, bind_tls=True).public_url
    log.info(f"Public URL: {public_url}")
    return public_url

async def launch():
    log.info("Starting SD-Trainer Mikazuki GUI...")
    log.info(f"Base directory: {base_dir_path()}, Working directory: {os.getcwd()}")
    log.info(f"{platform.system()} Python {platform.python_version()} {sys.executable}")

    if not args.skip_prepare_environment:
        prepare_environment(disable_auto_mirror=args.disable_auto_mirror)

    if not check_port_avaliable(args.port):
        avaliable = find_avaliable_ports(30000, 30000+20)
        if avaliable:
            args.port = avaliable
        else:
            log.error("port finding fallback error")
            sys.exit(1)

    log.info(f"SD-Trainer Version: {git_tag(base_dir_path())}")

    os.environ["MIKAZUKI_HOST"] = args.host
    os.environ["MIKAZUKI_PORT"] = str(args.port)
    os.environ["MIKAZUKI_TENSORBOARD_HOST"] = args.tensorboard_host
    os.environ["MIKAZUKI_TENSORBOARD_PORT"] = str(args.tensorboard_port)
    os.environ["MIKAZUKI_DEV"] = "1" if args.dev else "0"

    if args.listen:
        args.host = "0.0.0.0"
        args.tensorboard_host = "0.0.0.0"

    # Setup ngrok for public access
    public_url = setup_ngrok(args.port)

    if not args.disable_tageditor:
        run_tag_editor()

    if not args.disable_tensorboard:
        run_tensorboard()

    import uvicorn
    log.info(f"Server started at http://{args.host}:{args.port}")
    log.info(f"Accessible publicly at: {public_url}")
    # Run uvicorn in a non-blocking way for Colab
    config = uvicorn.Config("mikazuki.app:app", host=args.host, port=args.port, log_level="error", reload=args.dev)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    args, _ = parser.parse_known_args()
    if platform.system() == "Emscripten":
        asyncio.ensure_future(launch())
    else:
        asyncio.run(launch())
