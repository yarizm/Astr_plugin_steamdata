# AstrBot Steam 游戏查询插件

`astrbot_plugin_steamdata` 是一个专为 [AstrBot](https://github.com/Soulter/AstrBot) 设计的 Steam 数据查询插件。它能够响应用户的自然语言，从 Steam 官方商店 API 提取指定游戏的详细信息，并通过 LLM 将海量数据整合为优雅易读的总结报告，提供流畅的游戏资讯查询体验。

## ✨ 核心特性

- 🤖 **深度集成 Function Calling**: 无需刻意记忆指令，只需像往常一样和机器人聊天（如：“我想看 steam 上的 黑神话悟空”），LLM 即可自动调起工具检索数据。
- 📊 **全面的游戏数据获取**: 
  - 基础信息：开发商、发行日期、支持平台及类型。
  - 动态价格：实时查询当前售价及折扣力度。
  - 在线热度：通过 Steam Web API 获取当前活跃在线人数。
  - 真实口碑：总体评分统计（好评率）以及多条具有代表性的中英文玩家最新评价。
- ⌨️ **命令兜底支持**: 对于未开启大模型函数调用（Function Calling）的场景，依然提供 `/steam <游戏名>` 作为手动指令查询入口。

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
| `steam_api_key` | `string` | 空 | Steam Web API Key。**只有填入此项，才能正常获取游戏的“当前在线人数”**。可以在 [这里申请](https://steamcommunity.com/dev/apikey)。留空时插件将正常工作，仅跳过人数查询。 |
| `price_region` | `string` | `cn` | 价格和货币的结算区域代码（默认中国区）。 |
| `review_count` | `number` | `5` | 获取并提供给 LLM 参考的最新评论数量。 |
| `request_timeout` | `number` | `15` | 网络请求超时时间（秒）。 |
| `enable_fallback_commands` | `boolean`| `true` | 是否开启兜底的手动 `/steam` 指令。 |

## 🕹️ 使用示例

### 自然语言触发 (推荐)
直接与 AstrBot 对话即可触发：
> **User**: “帮我看看 steam 上的 Elden Ring 多少钱，口碑怎么样？”
> 
> **AstrBot**: (自动触发搜素，总结后回复) 
> “🎮 **Elden Ring** 目前国区售价为 ¥298。
> 它的近期口碑非常不错，总计获得了超过 50 万条评价，好评率达到了 92%（特别好评）。
> 在线热度也很高，当前有大约 6 万人正在交界地受苦！玩家们普遍称赞它的开放世界设计……”

### 指令触发
> `/steam 艾尔登法环`
> 
> (将直接返回系统格式化后的 Markdown 数据，不会经过 LLM 二次总结)

## 🤝 贡献与反馈

如果你在使用过程中遇到了问题，或者有更好的 API 数据处理建议，欢迎提交 Issue 或 Pull Request！
