"""
Serendipity FM - HTML 解析脚本
从微信公众号保存的 HTML 文件中提取文章信息
"""

import os
import re
import json
import hashlib
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path


# 需要跳过的引导图关键词（公众号顶部引导关注的图片）
SKIP_IMAGE_KEYWORDS = [
    '风里雨里', '每天等你', '点击上方', '设为星标', '关注我们',
    '二维码', 'qrcode', 'logo', 'banner', '公众号'
]

# 需要跳过的图片 URL 模式
SKIP_IMAGE_PATTERNS = [
    r'wx_fmt=gif',  # 跳过 GIF 动图
    r'tp=webp',     # 某些小图标
]

# 中文语音角色池（Edge TTS）
VOICE_POOL = [
    "zh-CN-XiaoxiaoNeural",   # 女声 - 活泼
    "zh-CN-XiaoyiNeural",     # 女声 - 温柔
    "zh-CN-YunjianNeural",    # 男声 - 成熟
    "zh-CN-YunxiNeural",      # 男声 - 年轻
    "zh-CN-YunxiaNeural",     # 男声 - 少年
    "zh-CN-XiaohanNeural",    # 女声 - 知性（替换XiaochenNeural）
]


def get_voice_for_article(article_id: str) -> str:
    """根据文章ID确定性地分配一个语音角色"""
    hash_val = int(hashlib.md5(article_id.encode()).hexdigest(), 16)
    return VOICE_POOL[hash_val % len(VOICE_POOL)]


def should_skip_image(img_url: str, img_alt: str = "") -> bool:
    """判断图片是否应该被跳过"""
    # 检查 alt 文本
    alt_lower = img_alt.lower() if img_alt else ""
    for keyword in SKIP_IMAGE_KEYWORDS:
        if keyword in alt_lower:
            return True
    
    # 检查 URL 模式
    for pattern in SKIP_IMAGE_PATTERNS:
        if re.search(pattern, img_url, re.IGNORECASE):
            return True
    
    return False


def extract_content_image(soup: BeautifulSoup) -> str | None:
    """
    从正文中提取合适的封面图
    跳过顶部引导图，选择正文中有意义的配图
    """
    # 查找正文容器
    content_div = soup.find('div', id='js_content')
    if not content_div:
        content_div = soup.find('div', class_='rich_media_content')
    
    if not content_div:
        return None
    
    # 获取所有图片
    images = content_div.find_all('img')
    
    for img in images:
        # 获取图片 URL（可能在不同属性中）
        img_url = img.get('data-src') or img.get('src') or ''
        img_alt = img.get('alt', '')
        
        if not img_url or img_url.startswith('data:'):
            continue
        
        # 跳过引导图
        if should_skip_image(img_url, img_alt):
            continue
        
        # 检查图片尺寸（如果有的话）
        width = img.get('data-w') or img.get('width')
        if width:
            try:
                w = int(width)
                if w < 200:  # 跳过太小的图片
                    continue
            except ValueError:
                pass
        
        return img_url
    
    return None


def extract_author(soup: BeautifulSoup, text_content: str) -> str:
    """
    提取作者信息
    优先从正文开头提取，备选 meta 标签
    """
    # 尝试从正文开头匹配作者（常见格式）
    author_patterns = [
        r'^([A-Za-z\u4e00-\u9fa5]{1,10})\s+每日豆瓣',  # "K 每日豆瓣"
        r'作者[：:]\s*([A-Za-z\u4e00-\u9fa5]{1,20})',
        r'文[/／]\s*([A-Za-z\u4e00-\u9fa5]{1,20})',
        r'by\s+([A-Za-z\u4e00-\u9fa5]{1,20})',
    ]
    
    # 只检查前500个字符
    head_text = text_content[:500]
    
    for pattern in author_patterns:
        match = re.search(pattern, head_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # 尝试查找特定的作者元素
    author_elem = soup.find('span', class_='rich_media_meta_text')
    if author_elem:
        author_text = author_elem.get_text(strip=True)
        # 修复：去除重复的作者名（有时会重复两次）
        if len(author_text) > 2:
            half_len = len(author_text) // 2
            if author_text[:half_len] == author_text[half_len:]:
                author_text = author_text[:half_len]
        return author_text
    
    # 备选：从 meta 标签获取
    meta_author = soup.find('meta', attrs={'name': 'author'})
    if meta_author:
        author = meta_author.get('content', '')
        if author and author != '豆瓣用户':
            return author
    
    return "佚名"


def extract_title(soup: BeautifulSoup) -> str:
    """提取文章标题"""
    # 优先从 og:title 获取
    og_title = soup.find('meta', property='og:title')
    if og_title:
        return og_title.get('content', '').strip()
    
    # 备选：从 title 标签获取
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    
    return "未命名文章"


def extract_description(soup: BeautifulSoup) -> str:
    """提取文章描述"""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        return meta_desc.get('content', '').strip()
    
    og_desc = soup.find('meta', property='og:description')
    if og_desc:
        return og_desc.get('content', '').strip()
    
    return ""


def clean_text_for_tts(text: str) -> str:
    """
    清理文本，使其适合 TTS 朗读
    """
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text)
    
    # 移除特殊标记
    text = re.sub(r'点击上方.*?设为星标', '', text)
    text = re.sub(r'本文来自豆瓣.*?原创内容', '', text)
    text = re.sub(r'感谢作者为豆瓣提供优质原创内容', '', text)
    text = re.sub(r'由豆瓣用户.*?授权发布', '', text)
    text = re.sub(r'原文标题[：:][^\n]+', '', text)
    
    # 移除 URL
    text = re.sub(r'https?://\S+', '', text)
    
    # 移除表情符号（保留常见中文标点）
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    
    # 移除多余的标点
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'[！]{2,}', '！', text)
    text = re.sub(r'[？]{2,}', '？', text)
    
    return text.strip()


def extract_text_content(soup: BeautifulSoup) -> str:
    """提取正文纯文本内容"""
    content_div = soup.find('div', id='js_content')
    if not content_div:
        content_div = soup.find('div', class_='rich_media_content')
    
    if not content_div:
        return ""
    
    # 获取纯文本
    text = content_div.get_text(separator='\n', strip=True)
    
    # 清理文本
    text = clean_text_for_tts(text)
    
    return text


def parse_html_file(file_path: str) -> dict | None:
    """
    解析单个 HTML 文件，提取所有需要的信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ 无法读取文件 {file_path}: {e}")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取各项信息
    title = extract_title(soup)
    text_content = extract_text_content(soup)
    author = extract_author(soup, text_content)
    description = extract_description(soup)
    cover_url = extract_content_image(soup)
    
    if not text_content or len(text_content) < 100:
        print(f"⚠️ 文章内容太短，跳过: {title}")
        return None
    
    # 生成唯一 ID
    file_name = os.path.basename(file_path)
    article_id = hashlib.md5(file_name.encode()).hexdigest()[:8]
    
    # 分配语音角色
    voice = get_voice_for_article(article_id)
    
    # 来源固定为"每日豆瓣"（可以后续根据不同来源扩展）
    source = "每日豆瓣"
    
    # 经典语句使用 description
    quote = description if description else ""
    
    return {
        "id": article_id,
        "title": title,
        "author": author,
        "source": source,
        "quote": quote,
        "description": description,
        "text_content": text_content,
        "cover_url": cover_url,
        "voice": voice,
        "source_file": file_name,
        "audio_file": f"audio/{article_id}.mp3",
        "cover_file": f"covers/{article_id}.jpg" if cover_url else None
    }


def download_cover_image(url: str, save_path: str) -> bool:
    """下载封面图片"""
    try:
        # 添加 User-Agent 避免被拦截
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"⚠️ 下载图片失败: {e}")
        return False


def parse_all_html_files(source_dir: str, output_dir: str) -> list[dict]:
    """
    解析目录下所有 HTML 文件
    """
    html_files = list(Path(source_dir).glob("*.html"))
    
    if not html_files:
        print(f"❌ 在 {source_dir} 目录下没有找到 HTML 文件")
        return []
    
    print(f"📂 找到 {len(html_files)} 个 HTML 文件")
    
    episodes = []
    
    for html_file in html_files:
        print(f"\n📄 解析: {html_file.name}")
        
        result = parse_html_file(str(html_file))
        
        if result:
            # 下载封面图
            if result['cover_url']:
                cover_path = os.path.join(output_dir, result['cover_file'])
                if download_cover_image(result['cover_url'], cover_path):
                    print(f"  ✅ 封面图已下载")
                else:
                    result['cover_file'] = None
            
            episodes.append(result)
            print(f"  ✅ 标题: {result['title']}")
            print(f"  ✅ 作者: {result['author']}")
            print(f"  ✅ 语音: {result['voice']}")
            print(f"  ✅ 内容长度: {len(result['text_content'])} 字")
    
    return episodes


def save_episodes_data(episodes: list[dict], output_path: str):
    """保存节目数据到 JSON 文件"""
    # 移除 text_content 字段（太长，单独保存）
    episodes_meta = []
    
    for ep in episodes:
        meta = {k: v for k, v in ep.items() if k != 'text_content'}
        meta['duration'] = 0  # 稍后由音频生成脚本更新
        episodes_meta.append(meta)
        
        # 保存文本内容到单独文件（供 TTS 使用）
        text_path = output_path.replace('episodes.json', f"texts/{ep['id']}.txt")
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(ep['text_content'])
    
    # 保存元数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"episodes": episodes_meta}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 节目数据已保存到: {output_path}")


def main():
    # 项目根目录
    project_dir = Path(__file__).parent.parent
    
    # HTML 源文件目录（直接使用项目根目录，因为 HTML 文件就在那里）
    source_dir = project_dir
    
    # 输出目录
    output_dir = project_dir
    
    print("=" * 50)
    print("🎙️ Serendipity FM - HTML 解析器")
    print("=" * 50)
    
    # 解析所有 HTML 文件
    episodes = parse_all_html_files(str(source_dir), str(output_dir))
    
    if not episodes:
        print("\n❌ 没有成功解析任何文章")
        return
    
    # 保存数据
    output_path = os.path.join(output_dir, "data", "episodes.json")
    save_episodes_data(episodes, output_path)
    
    print(f"\n🎉 成功解析 {len(episodes)} 篇文章！")
    print("下一步：运行 generate_audio.py 生成语音")


if __name__ == "__main__":
    main()
