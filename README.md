# 📈 TrendRadar: Financial Intelligence Pipeline

## 📝 项目愿景
本项目旨在打造一个全自动化的**金融投资情报系统**。通过 TrendRadar 实时监控全网财经热点（雪球、财新、华尔街见闻、金十数据），利用 AI 进行深度投研分析，并自动生成适合投资者收听的**深度财经播客**，推送到飞书等平台。

## 🏗️ 系统架构

### 1. 情报搜集与分析 (TrendRadar)
- **功能**: 24小时监控各大财经媒体 RSS 及热搜榜单。
- **数据源**: 华尔街见闻、财新网、金十数据、雪球、Yahoo 财经等。
- **AI 分析**: 针对**沪深300**、**科技成长股**、**黄金避险**三大板块进行深度研判。
- **产物**: 每日生成包含 AI 研报的 HTML 页面，并推送 Markdown 简报至飞书。

### 2. 自动化桥接 (Bridge)
- **功能**: 监听 TrendRadar 生成的最新研报。
- **处理**: 提取 HTML 中的 AI 分析结论和热点新闻。
- **脚本生成**: 调用 DeepSeek API，将枯燥的研报转化为**“老张与陈老师”**的财经对谈脚本（茶馆聊天风格）。
- **分发**: 将脚本发送给 Hacker-Podcast 服务。

### 3. 音频生成 (Hacker-Podcast)
- **功能**: 接收自定义脚本，生成多角色对话音频。
- **技术**: 使用 TTS 技术生成逼真的对话播客。

## 🚀 快速开始

### 1. 配置
修改 `TrendRadar/config/config.yaml` 配置您的 API Key 和推送渠道。

### 2. 启动服务
使用 Docker Compose 一键启动所有服务：

```bash
docker-compose up -d
```

### 3. 运行流程
1. **TrendRadar** 抓取财经新闻 -> 生成 HTML 研报 -> 推送文字版到飞书。
2. **Bridge** 检测到新研报 -> 生成播客脚本 -> 发送给 Worker。
3. **Hacker-Podcast** 生成 MP3 音频 -> 存储到 R2/KV。

## 📊 分析板块说明
系统会自动针对以下三个核心板块输出观点：
1. **国内股票 (CSI 300)**: 关注权重股、宏观经济数据及政策风向。
2. **科技股 (Tech)**: 关注 AI、半导体、新能源及美股映射效应。
3. **黄金 (Gold)**: 关注美联储利率、美元指数及地缘避险情绪。

## 🛠️ 技术栈
- Python (TrendRadar, Bridge)
- TypeScript/Cloudflare Workers (Hacker-Podcast)
- DeepSeek V3 (AI Analysis & Script Generation)
- Docker
