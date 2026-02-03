# 🎲 Serendipity FM

> 人类终将在声音的旷野里相遇。

一个随机播放豆瓣播客的网页应用，让你在偶然中发现惊喜。

![Serendipity FM 主界面](https://raw.githubusercontent.com/JieGaoSunny/serendipity-fm/main/screenshots/main.png)

## ✨ 特性

- 🎵 **随机播放** - 每次刷新都是一期新的播客内容
- 🌊 **流动光晕背景** - 基于 Three.js 的绿色波浪动画，支持鼠标视差交互
- 💚 **收藏功能** - 喜欢的内容可以点心收藏
- ⏭️ **跳过功能** - 不感兴趣直接下一个
- 📱 **响应式设计** - 完美适配手机、平板、电脑
- 🎨 **Apple 风格 UI** - 毛玻璃卡片、圆角设计

## 🖼️ 截图预览

### 桌面端
![桌面端界面](https://raw.githubusercontent.com/JieGaoSunny/serendipity-fm/main/screenshots/desktop.png)

### 播放状态
![播放中](https://raw.githubusercontent.com/JieGaoSunny/serendipity-fm/main/screenshots/playing.png)

### 移动端
![移动端界面](https://raw.githubusercontent.com/JieGaoSunny/serendipity-fm/main/screenshots/mobile.png)

## 🚀 在线体验

访问：**https://jiegaosunny.github.io/serendipity-fm/**

## 📁 项目结构

```
serendipity-fm/
├── index.html          # 主页面
├── data/
│   ├── episodes.json   # 播客数据
│   └── texts/          # 播客文字内容
├── audio/              # 音频文件 (MP3)
├── covers/             # 封面图片
├── sourcedata/         # 原始 HTML 数据源
├── scripts/            # Python 处理脚本
│   ├── parse_html.py   # 解析 HTML 提取数据
│   ├── generate_audio.py # 生成 TTS 音频
│   ├── update_json.py  # 更新 JSON 数据
│   └── fix_authors.py  # 修复作者名称
├── exampleUX.html      # React 组件示例
└── PRD_SerendipityFM.md # 产品需求文档
```

## 🛠️ 本地运行

### 方法 1: Python HTTP Server（推荐）

```bash
# 克隆仓库
git clone https://github.com/JieGaoSunny/serendipity-fm.git
cd serendipity-fm

# 启动本地服务器
python3 -m http.server 8080

# 打开浏览器访问
open http://localhost:8080
```

### 方法 2: VS Code Live Server

1. 安装 VS Code 插件 "Live Server"
2. 右键 `index.html` → "Open with Live Server"

## 📝 如何添加新内容

### 1. 准备 HTML 源文件

将豆瓣播客的 HTML 页面保存到 `sourcedata/` 文件夹

### 2. 解析并生成数据

```bash
# 安装依赖
pip install -r requirements.txt

# 解析 HTML 并提取数据
python scripts/parse_html.py

# 生成 TTS 音频（需要配置 Azure TTS）
python scripts/generate_audio.py

# 更新 episodes.json
python scripts/update_json.py
```

### 3. 数据格式

`data/episodes.json` 结构：

```json
{
  "episodes": [
    {
      "id": "abc123",
      "title": "播客标题",
      "author": "作者名",
      "quote": "精选语录",
      "cover": "covers/abc123.jpg",
      "audio": "audio/abc123.mp3",
      "text": "data/texts/abc123.txt"
    }
  ]
}
```

## 🎨 技术栈

- **前端**: 纯 HTML/CSS/JavaScript（无框架依赖）
- **背景动画**: Three.js WebGL Shader
- **音频**: Web Audio API
- **字体**: SF Pro + Cormorant Garamond
- **TTS**: Azure Cognitive Services（可选）

## ⌨️ 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `空格` | 播放/暂停 |
| `→` | 下一个 |
| `L` | 喜欢/取消喜欢 |

## 📄 License

MIT License

## 🙏 致谢

- 内容来源：豆瓣用户分享
- 背景动画灵感：[ReactBits Floating Lines](https://www.reactbits.dev/backgrounds/floating-lines)
- UI 设计参考：Apple Music

---

**Made with ❤️ by Serendipity FM**