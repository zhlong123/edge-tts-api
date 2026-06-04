# Edge TTS API

> OpenAI 兼容的微软 Edge TTS 独立语音合成服务 — 零成本、零 Key、任何支持 OpenAI `/v1/audio/speech` 的客户端都能直接对接

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![Edge TTS](https://img.shields.io/badge/Edge%20TTS-7.2.6-0078D4?logo=microsoftedge&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)
![OpenAI Compatible](https://img.shields.io/badge/OpenAI-compatible-10A37F?logo=openai&logoColor=white)

---

## ✨ 特性

- **OpenAI 兼容** — `POST /v1/audio/speech` 直接对接任何 OpenAI TTS 客户端（openai-python / LangChain / Dify / Open WebUI / LobeChat 等）
- **零成本** — 走微软 Edge TTS 公网接口，不需要 Azure Key
- **Windows 友好** — 自带中文 bat 菜单（GBK 编码），双击即可启动
- **可插拔鉴权** — Bearer Token 按需开关
- **音色预设** — `config/voice_presets.json` 中文 20+ 音色
- **命令行工具** — `python manage.py` 提供 show-config / set-voice / health / test-tts 等子命令

---

## 🚀 快速开始

### Windows（推荐）

双击 `edge-tts-api.bat`，弹出中文菜单：

```
================================
   Edge TTS API 管理菜单
================================
[1] 安装依赖
[2] 启动服务
[3] 切换默认音色
[4] 切换服务端口
[5] 开启/关闭 API 鉴权
[6] 测试合成
[7] 查看服务状态
[0] 退出
================================
```

**首次使用**：先选 `[1]`，再选 `[2]`。

> 菜单文件 `edge-tts-menu.bat` 由 `build_bat.py` 生成（GBK 编码）。  
> 如需改菜单文字：编辑 `build_bat.py` → `python build_bat.py` 重新生成。

### macOS / Linux

```bash
git clone https://github.com/zhlong123/edge-tts-api.git
cd edge-tts-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

服务默认监听 `http://127.0.0.1:9880`。

---

## 🩺 健康检查

```bash
curl http://127.0.0.1:9880/health
# → {"status":"ok","default_voice":"zh-CN-XiaoxiaoNeural","port":9880}
```

---

## 🔊 API

### `POST /v1/audio/speech`

OpenAI 兼容的语音合成端点。

**请求**：

```json
{
  "model": "tts-1",
  "input": "你好，世界",
  "voice": "zh-CN-XiaoxiaoNeural",
  "response_format": "mp3",
  "speed": 1.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `model` | string | ❌ | 任意值（兼容 OpenAI），当前不区分 `tts-1` / `tts-1-hd` |
| `input` | string | ✅ | 要合成的文本 |
| `voice` | string | ❌ | Edge TTS 音色 ID，默认 `zh-CN-XiaoxiaoNeural` |
| `response_format` | string | ❌ | 当前**仅支持 `mp3`** |
| `speed` | float | ❌ | 0.25 - 4.0，1.0 为原速，映射到 Edge TTS `rate` |

**响应**：`audio/mpeg` 二进制。

**示例**（带鉴权）：

```bash
curl -X POST http://127.0.0.1:9880/v1/audio/speech \
  -H "Authorization: Bearer sk-edge-tts-local" \
  -H "Content-Type: application/json" \
  -d '{"input":"你好","voice":"zh-CN-XiaoxiaoNeural"}' \
  --output hello.mp3
```

### `GET /v1/voices`

返回 Edge TTS 公网所有可用音色（400+ 项）。

### `GET /v1/voices/presets`

返回本服务 `config/voice_presets.json` 维护的精选预设。

### `GET /v1/models`

```json
{"object":"list","data":[
  {"id":"tts-1","object":"model","owned_by":"edge-tts"},
  {"id":"tts-1-hd","object":"model","owned_by":"edge-tts"}
]}
```

---

## 🤖 通用 OpenAI 客户端接入

任何支持自定义 `base_url` 的 OpenAI 客户端都可以直接对接。把 `base_url` 指向本服务即可：

### openai-python 官方 SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-edge-tts-local",          # 本服务的 api_key,值见 config/settings.json
    base_url="http://127.0.0.1:9880/v1",  # OpenAI 兼容入口
)

resp = client.audio.speech.create(
    model="tts-1",
    voice="zh-CN-XiaoxiaoNeural",
    input="你好，世界",
)

with open("hello.mp3", "wb") as f:
    f.write(resp.read())
```

### curl

```bash
curl -X POST http://127.0.0.1:9880/v1/audio/speech \
  -H "Authorization: Bearer sk-edge-tts-local" \
  -H "Content-Type: application/json" \
  -d '{"input":"你好","voice":"zh-CN-XiaoxiaoNeural"}' \
  --output hello.mp3
```

### 其它框架

- **LangChain**：`ChatOpenAI(base_url="http://127.0.0.1:9880/v1", ...)` + 自定义 TTS 节点
- **Dify**：TTS 节点选 `OpenAI TTS`，填本服务 `api_url`
- **Open WebUI / LobeChat**：在 TTS 设置里把 OpenAI endpoint 改成 `http://127.0.0.1:9880/v1`

---

## ⚙️ 配置

编辑 `config/settings.json`：

```json
{
  "host": "0.0.0.0",
  "port": 9880,
  "api_key": "sk-edge-tts-local",
  "default_voice": "zh-CN-XiaoxiaoNeural",
  "require_auth": false
}
```

| 字段 | 默认值 | 说明 |
|---|---|---|
| `host` | `0.0.0.0` | 监听地址（`127.0.0.1` 仅本机访问）|
| `port` | `9880` | HTTP 端口 |
| `api_key` | `sk-edge-tts-local` | 鉴权 Token（`require_auth=true` 时必填） |
| `default_voice` | `zh-CN-XiaoxiaoNeural` | 默认音色 |
| `require_auth` | `false` | 是否开启 Bearer 鉴权 |

也可以用 `python manage.py set-voice <id>` / `set-port <port>` / `toggle-auth on` 改。

---

## 🗂️ 项目结构

```
edge-tts-api/
├── app/                      # FastAPI 应用
│   ├── __init__.py
│   ├── main.py               # 路由 + lifespan
│   ├── auth.py               # Bearer Token 鉴权
│   ├── config.py             # settings.json 读写
│   └── edge_engine.py        # Edge TTS 封装 (synthesize / voices)
├── config/
│   ├── settings.json         # 运行时配置 (端口/鉴权/默认音色)
│   └── voice_presets.json    # 精选音色预设
├── manage.py                 # 命令行工具 (供 bat 调用)
├── build_bat.py              # 生成 edge-tts-menu.bat 的脚本
├── edge-tts-api.bat          # 启动入口 (打开菜单)
├── edge-tts-menu.bat         # 中文菜单 (GBK)
├── test-bat.cmd              # 菜单自检
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠 命令行工具

```bash
python manage.py show-config            # 打印当前配置
python manage.py list-presets            # 列出所有预设音色
python manage.py set-voice <voice_id>    # 切换默认音色
python manage.py set-port <port>         # 切换端口
python manage.py toggle-auth on|off      # 开关鉴权
python manage.py health                  # 健康检查
python manage.py test-tts "你好" out.mp3 # 测试合成
```

---

## ❓ 常见问题

**Q: 启动后访问 `127.0.0.1:9880/health` 报 Connection refused**  
A: 看 `logs/server.log`（如果写了日志），或检查 `python manage.py is-running`。

**Q: 合成返回 502 "Edge TTS 合成失败"**  
A: Edge TTS 走公网，需要能访问微软服务器。开 VPN / 代理可能反而不通（被 SNI 拦截）。直连国内网络即可。

**Q: `response_format=wav` 报 400**  
A: 当前仅支持 `mp3`。要扩展可以加 `pydub` + `ffmpeg` 转码，欢迎 PR。

**Q: 怎么加新音色？**  
A: 编辑 `config/voice_presets.json`，加 `{"id": <n>, "name": "...", "lang": "...", "voice": "..."}`。`voice` 字段必须是 `GET /v1/voices` 返回列表里 `ShortName` 的值。

---

## 🧪 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 本地启动 (热重载)
uvicorn app.main:app --host 0.0.0.0 --port 9880 --reload

# 改菜单后重新生成
python build_bat.py
```

OpenAPI 文档：`http://127.0.0.1:9880/docs`

---

## 📜 License

MIT
