# AstrBot Steam 游戏查询插件

`astrbot_plugin_steamdata` 是为 [AstrBot](https://github.com/Soulter/AstrBot) 开发的 Steam 数据查询插件。它能够通过 Steam 官方 API 获取游戏详情及用户数据，并格式化后交由大语言模型（LLM）总结输出。

## ✨ 功能特性

- 🤖 **Function Calling 支持**: 支持模型自动识别意图并调用工具检索数据（如：“我想看 steam 上的 黑神话悟空”或“查查 XXX 的 CS2 库存”）。
- 📊 **游戏数据查询**: 
  - 基础信息：开发商、发行日期、支持平台及类型。
  - 价格信息：查询当前售价及折扣。
  - 在线人数：通过 Steam Web API 获取当前活跃在线人数。
  - 评价信息：获取总体评分（好评率）及最新评价抽样。
- 👤 **玩家状态与游戏库**: 
  - 支持通过 SteamID 或自定义 URL（Vanity URL）解析玩家。
  - 获取玩家在线状态、当前游玩游戏及最近两周活跃游戏时长。
- 🎒 **游戏库存查询**:
  - 提取指定游戏（如 CS2、Dota 2）的前排库存物品信息。
- ⌨️ **常规指令支持**: 提供了 `/steam`、`/steam_user` 和 `/steam_inv` 作为基础文本指令入口，供未开启 Function Calling 的环境使用。

## 📦 安装说明

1. 确保你已安装 [AstrBot](https://github.com/Soulter/AstrBot) 且正常运行。
2. 将本项目的 `astrbot_plugin_steamdata` 文件夹拷贝到 AstrBot 的 `data/plugins/` 目录下。
3. 也可以通过 Git Clone 直接放入插件目录：
   ```bash
   cd data/plugins
   git clone https://github.com/yarizm/Astr_plugin_steamdata.git astrbot_plugin_steamdata
   ```
4. 进入插件目录并安装所需依赖：
   ```bash
   cd astrbot_plugin_steamdata
   pip install -r requirements.txt
   ```
5. 重启 AstrBot。

## ⚙️ 插件配置

插件安装并被 AstrBot 加载后，你可以在控制台界面（或 `config.yaml` 中）看到以下配置项：

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :---: | :--- | :--- |
| `steam_api_key` | `string` | 空 | Steam Web API Key。**只有填入此项，才能正常获取游戏的“当前在线人数”、玩家状态、游戏库和库存**。可以在 [这里申请](https://steamcommunity.com/dev/apikey)。留空时插件仍可查询游戏基本信息。 |
| `price_region` | `string` | `cn` | 价格和货币的结算区域代码（默认中国区）。 |
| `review_count` | `int` | `5` | 获取并提供给 LLM 参考的最新评论数量。 |
| `request_timeout` | `int` | `15` | 网络请求超时时间（秒）。 |
| `enable_fallback_commands` | `bool`| `true` | 是否开启兜底的手动 `/steam` 系列指令。 |

## 🕹️ 使用示例

### 自然语言触发 (推荐)
直接与 AstrBot 对话即可触发（确保模型支持并开启了 Function Calling）：
> **User**: “帮我看看 steam 上的 Elden Ring 多少钱，口碑怎么样？”
> 
> **AstrBot**: (触发工具调用，返回总结) 
> “**Elden Ring** 目前国区售价为 ¥298。总计获得约 50 万条评价，好评率 92%（特别好评）。当前约有 6 万人在线...”
> 
> **User**: “看看 XXX 最近在玩什么游戏？”
> 
> **AstrBot**: “玩家 **XXX** 目前在线。最近两周主要在游玩 CS2（时长 40 小时）。此外库中还拥有...”

### 指令触发
如果未开启大模型工具调用，你可以直接使用以下命令（返回系统直接格式化后的 Markdown 数据）：
> `/steam 艾尔登法环` —— 查询游戏信息
> `/steam_user XXX` —— 查询玩家状态
> `/steam_inv XXX CS2` —— 查询玩家指定游戏的库存

## 🤝 贡献与反馈

如果你在使用过程中遇到了问题，或者有更好的 API 数据处理建议，欢迎提交 Issue 或 Pull Request！
