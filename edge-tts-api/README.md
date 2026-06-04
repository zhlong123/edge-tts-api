# Edge TTS API

OpenAI 兼容的 Edge TTS 独立语音合成服务，可从本仓库其他程序通过 HTTP 调用。

## 快速开始

1. 双击运行 `edge-tts-api.bat`（会打开中文菜单 `edge-tts-menu.bat`）
2. 菜单选择 `[1] 安装依赖`（首次使用）
3. 选择 `[2] 启动服务`
4. 选择 `[6] 测试合成` 验证

> 说明：中文菜单由 `build_bat.py` 生成（GBK 编码，适配中文 Windows）。如需改菜单文字，请编辑 `build_bat.py` 后运行 `python build_bat.py`。

默认地址：`http://127.0.0.1:9880`

## API

### 健康检查

`GET /health`

### OpenAI 兼容合成

`POST /v1/audio/speech`

```json
{
  "model": "tts-1",
  "input": "你好，世界",
  "voice": "zh-CN-XiaoxiaoNeural",
  "response_format": "mp3",
  "speed": 1.0
}
```

### 预设音色

`GET /v1/voices/presets`

## 接入小智 xiaozhi-server

在 `config.yaml` 中配置：

```yaml
selected_module:
  TTS: OpenAITTS

TTS:
  OpenAITTS:
    type: openai
    api_key: sk-edge-tts-local
    api_url: http://127.0.0.1:9880/v1/audio/speech
    model: tts-1
    voice: zh-CN-XiaoxiaoNeural
    speed: 1
    format: mp3
    output_dir: tmp/
```

## 配置

编辑 `config/settings.json`：

| 字段 | 说明 |
|------|------|
| `port` | 服务端口，默认 9880 |
| `default_voice` | 默认音色 |
| `api_key` | 鉴权密钥 |
| `require_auth` | 是否启用 Bearer 鉴权 |

也可通过 bat 菜单切换音色、端口和鉴权。

## 注意事项

- 需要能访问微软 Edge TTS 网络；开 VPN/代理可能导致失败
- 当前仅支持 `response_format=mp3`
- `speed` 会近似映射到 Edge TTS 的语速参数
