"""命令行工具，供 bat 脚本调用。"""

import ipaddress
import json
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.config import (  # noqa: E402
    load_settings,
    load_voice_presets,
    save_settings,
    update_default_voice,
)


def cmd_show_config() -> int:
    settings = load_settings()
    print(json.dumps(settings, ensure_ascii=False, indent=2))
    return 0


def cmd_list_presets() -> int:
    presets = load_voice_presets()
    current = load_settings().get("default_voice", "")
    for item in presets:
        mark = " *" if item["voice"] == current else ""
        print(f"{item['id']:>2}. {item['name']} [{item['lang']}]{mark}")
        print(f"    {item['voice']}")
    return 0


def cmd_set_voice(voice: str) -> int:
    update_default_voice(voice)
    print(f"默认音色已设置为: {voice}")
    return 0


def cmd_set_voice_by_id(preset_id: str) -> int:
    presets = load_voice_presets()
    for item in presets:
        if str(item["id"]) == str(preset_id):
            return cmd_set_voice(item["voice"])
    print(f"未找到编号 {preset_id} 的音色")
    return 1


def cmd_set_port(port: str) -> int:
    settings = load_settings()
    settings["port"] = int(port)
    save_settings(settings)
    print(f"端口已设置为: {port}")
    return 0


def cmd_toggle_auth(enable: str) -> int:
    settings = load_settings()
    settings["require_auth"] = enable.lower() in ("1", "true", "yes", "on")
    save_settings(settings)
    state = "开启" if settings["require_auth"] else "关闭"
    print(f"API 鉴权已{state}")
    return 0


def cmd_health() -> int:
    settings = load_settings()
    port = settings.get("port", 9880)
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            return 0
    except urllib.error.URLError as exc:
        print(f"服务未运行或无法连接: {exc}")
        return 1


def cmd_test_tts(text: str, output: str) -> int:
    settings = load_settings()
    port = settings.get("port", 9880)
    url = f"http://127.0.0.1:{port}/v1/audio/speech"
    payload = json.dumps(
        {
            "model": "tts-1",
            "input": text,
            "voice": settings.get("default_voice"),
            "response_format": "mp3",
            "speed": 1.0,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if settings.get("require_auth"):
        headers["Authorization"] = f"Bearer {settings.get('api_key', '')}"

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
            print(f"测试音频已保存: {out_path.resolve()}")
            return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"请求失败 HTTP {exc.code}: {detail}")
        return 1
    except urllib.error.URLError as exc:
        print(f"请求失败: {exc}")
        return 1


def cmd_get_port() -> int:
    print(load_settings().get("port", 9880))
    return 0


def cmd_get_voice() -> int:
    print(load_settings().get("default_voice", "zh-CN-XiaoxiaoNeural"))
    return 0


def cmd_is_running() -> int:
    return cmd_health()


def _is_ipv4(s: str) -> bool:
    try:
        ipaddress.IPv4Address(s)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def _list_lan_ips() -> list[str]:
    """列出本机所有非回环 IPv4 地址，按字典序去重。"""
    ips: set[str] = set()
    # 方法 1: 解析 hostname
    try:
        for info in socket.gethostbyname_ex(socket.gethostname()):
            items = info if isinstance(info, list) else [info]
            for ip in items:
                if _is_ipv4(ip) and not ip.startswith("127."):
                    ips.add(ip)
    except socket.gaierror:
        pass
    # 方法 2: 通过 UDP 套接字让内核给出对外 IP(不发包)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("223.5.5.5", 80))
            ips.add(s.getsockname()[0])
        finally:
            s.close()
    except OSError:
        pass
    return sorted(ips)


def cmd_lan_url() -> int:
    """打印本机所有可局域网访问的 URL,每行一个。"""
    settings = load_settings()
    port = int(settings.get("port", 9880))
    host = settings.get("host", "0.0.0.0")

    if host not in ("0.0.0.0", "::"):
        # 绑了特定 IP,直接用
        print(f"http://{host}:{port}/")
        return 0

    ips = _list_lan_ips()
    if not ips:
        print(f"# 未发现可局域网访问的网卡 IP,127.0.0.1 仍可用")
        print(f"http://127.0.0.1:{port}/")
        return 0
    for ip in ips:
        print(f"http://{ip}:{port}/")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: manage.py <command> [args...]")
        return 1

    command = sys.argv[1]
    if command == "get-port":
        return cmd_get_port()
    if command == "get-voice":
        return cmd_get_voice()
    if command == "is-running":
        return cmd_is_running()
    if command == "lan-url":
        return cmd_lan_url()
    if command == "show-config":
        return cmd_show_config()
    if command == "list-presets":
        return cmd_list_presets()
    if command == "set-voice" and len(sys.argv) >= 3:
        return cmd_set_voice(sys.argv[2])
    if command == "set-voice-id" and len(sys.argv) >= 3:
        return cmd_set_voice_by_id(sys.argv[2])
    if command == "set-port" and len(sys.argv) >= 3:
        return cmd_set_port(sys.argv[2])
    if command == "toggle-auth" and len(sys.argv) >= 3:
        return cmd_toggle_auth(sys.argv[2])
    if command == "health":
        return cmd_health()
    if command == "test-tts":
        text = sys.argv[2] if len(sys.argv) >= 3 else "你好，这是 Edge TTS 测试。"
        output = sys.argv[3] if len(sys.argv) >= 4 else str(ROOT / "output" / "test.mp3")
        return cmd_test_tts(text, output)

    print(f"未知命令: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
