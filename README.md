# AstrBot Steam 数据查询插件

## 简介

`astrbot_plugin_steamdata` 是适用于 AstrBot 的 Steam 官方数据查询插件。插件通过 Steam Store API、Steam Web API 和 Steam Community 公开接口查询游戏信息、玩家状态和公开库存，并以 Markdown 文本返回给 AstrBot。

插件目录为仓库根目录，入口文件为 `main.py`。

## 功能特性

- 查询 Steam 游戏基础信息、商店链接、价格、评价和最新评论。
- 在配置 Steam Web API Key 后查询游戏当前在线人数。
- 在配置 Steam Web API Key 后查询玩家在线状态、正在游玩的游戏和游戏库概览。
- 查询指定玩家在指定游戏中的公开库存。
- 支持 AstrBot LLM Tool 调用。
- 支持 `/steam`、`/steam_user`、`/steam_inv` 兜底命令。

## 安装要求

- AstrBot 版本：`>=4.16,<5`
- Python 版本：建议 Python 3.10 或更高
- Python 依赖：`aiohttp`

如果未来插件代码改用更高版本 AstrBot API，请同步调整 `metadata.yaml` 中的 `astrbot_version`。

## 安装方式

将仓库放入 AstrBot 的插件目录，例如：

```bash
cd data/plugins
git clone https://github.com/yarizm/Astr_plugin_steamdata.git Astr_plugin_steamdata
```

确认 AstrBot 能读取到插件包目录：

```text
data/plugins/Astr_plugin_steamdata/main.py
```

安装依赖：

```bash
cd data/plugins/Astr_plugin_steamdata
python -m pip install -r requirements.txt
```

安装完成后重启 AstrBot。

## 配置说明

插件配置文件由 AstrBot 根据 `_conf_schema.json` 生成。Steam Web API Key 可以在 [Steam Web API Key 页面](https://steamcommunity.com/dev/apikey) 申请。

不要把 `steam_api_key` 发布到公开仓库、截图、日志或聊天记录中。

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `steam_api_key` | string | 空 | Steam Web API Key。为空时游戏基础信息、价格和评论仍可查询，但在线人数、玩家状态、游戏库、Vanity URL 解析等能力会降级或不可用。 |
| `price_region` | string | `cn` | Steam 商店价格区域代码，例如 `cn`、`us`、`jp`。 |
| `review_count` | int | `5` | 每次查询拉取的最新评论数量，建议范围 `1-50`。 |
| `request_timeout` | int | `15` | Steam HTTP 请求超时时间，单位秒，建议范围 `3-60`。 |
| `enable_fallback_commands` | bool | `true` | 是否启用 `/steam`、`/steam_user`、`/steam_inv` 兜底命令。 |

## 使用方式

### 自然语言调用

当 AstrBot 使用的模型支持 Function Calling，并且工具未被禁用时，可以直接用自然语言提问，例如：

- `帮我查一下 Steam 上 Elden Ring 的价格和评价`
- `看看这个玩家最近在玩什么：<SteamID 或 Vanity URL>`
- `查一下 <SteamID 或 Vanity URL> 的 CS2 库存`

### 命令调用

| 命令 | 说明 |
|---|---|
| `/steam <游戏名>` | 查询 Steam 游戏信息 |
| `/steam_user <SteamID 或 Vanity URL>` | 查询玩家状态和最近游戏 |
| `/steam_inv <SteamID 或 Vanity URL> <游戏名>` | 查询指定玩家的指定游戏库存 |

## 功能降级说明

`steam_api_key` 为空时，插件不会崩溃，但以下能力会降级：

- 游戏基础信息、价格、评论：通常仍可查询。
- 游戏在线人数：不可用。
- 玩家状态、游戏库、Vanity URL 解析：不可用。
- 库存查询：使用 SteamID64 时仍可能可用；使用 Vanity URL 时需要 API Key 才能解析。

Steam 用户的在线状态、游戏库和库存还受用户隐私设置影响。即使配置了 API Key，如果玩家资料、游戏详情或库存不是公开状态，插件也可能只能返回空结果或隐私提示。

## 常见问题

**为什么玩家状态查不到？**

请确认已配置 `steam_api_key`，并确认玩家 Steam 资料不是私密状态。

**为什么库存为空？**

库存为空可能是玩家确实没有该游戏库存，也可能是 Steam 库存隐私设置不允许读取。

**为什么在线人数为空？**

在线人数依赖 Steam Web API Key。请确认 `steam_api_key` 已配置且没有失效。

**可以公开 API Key 吗？**

不可以。Steam Web API Key 属于敏感配置，不应出现在公开仓库、日志、截图或聊天记录中。

## 开发与测试

本地开发建议先安装依赖：

```bash
python -m pip install -r requirements.txt
python -m pip install ruff
```

执行基础检查：

```bash
python -m py_compile main.py
python -m unittest discover -s tests -v
ruff check .
git diff --check
```

如果本地没有安装 AstrBot，插件会在测试环境使用最小 fallback stub 通过导入和语法检查；真实 AstrBot 环境下会优先使用 AstrBot 的真实 API。

## 许可证

本项目使用 MIT License，详见 `LICENSE`。
