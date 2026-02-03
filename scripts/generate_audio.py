"""
Serendipity FM - 音频生成脚本
使用 Edge TTS 将文章文本转换为语音
"""

import os
import json
import asyncio
from pathlib import Path
from mutagen.mp3 import MP3

try:
    import edge_tts
except ImportError:
    print("❌ 请先安装 edge-tts: pip install edge-tts")
    exit(1)


async def generate_audio(text: str, voice: str, output_path: str) -> bool:
    """
    使用 Edge TTS 生成音频
    """
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"❌ 生成音频失败: {e}")
        return False


def get_audio_duration(file_path: str) -> int:
    """获取音频时长（秒）"""
    try:
        audio = MP3(file_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"⚠️ 无法获取音频时长: {e}")
        return 0


async def process_episode(episode: dict, project_dir: Path) -> dict | None:
    """处理单个节目，生成音频"""
    
    episode_id = episode['id']
    voice = episode['voice']
    
    # 读取文本内容
    text_path = project_dir / "data" / "texts" / f"{episode_id}.txt"
    if not text_path.exists():
        print(f"❌ 找不到文本文件: {text_path}")
        return None
    
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 音频输出路径
    audio_path = project_dir / episode['audio_file']
    
    # 如果音频已存在，跳过
    if audio_path.exists():
        print(f"  ⏭️ 音频已存在，跳过生成")
        duration = get_audio_duration(str(audio_path))
        episode['duration'] = duration
        return episode
    
    print(f"  🎙️ 正在生成音频...")
    print(f"  📝 文本长度: {len(text)} 字")
    print(f"  🗣️ 使用语音: {voice}")
    
    # 生成音频
    success = await generate_audio(text, voice, str(audio_path))
    
    if success:
        duration = get_audio_duration(str(audio_path))
        episode['duration'] = duration
        print(f"  ✅ 音频生成完成! 时长: {duration // 60}:{duration % 60:02d}")
        return episode
    else:
        return None


async def main():
    # 项目根目录
    project_dir = Path(__file__).parent.parent
    
    # 读取节目数据
    episodes_path = project_dir / "data" / "episodes.json"
    
    if not episodes_path.exists():
        print("❌ 找不到 episodes.json，请先运行 parse_html.py")
        return
    
    with open(episodes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    episodes = data.get('episodes', [])
    
    if not episodes:
        print("❌ 没有找到任何节目")
        return
    
    print("=" * 50)
    print("🎙️ Serendipity FM - 音频生成器")
    print("=" * 50)
    print(f"📋 共 {len(episodes)} 个节目待处理\n")
    
    # 确保音频目录存在
    (project_dir / "audio").mkdir(exist_ok=True)
    
    # 处理每个节目
    updated_episodes = []
    success_count = 0
    
    for i, episode in enumerate(episodes, 1):
        print(f"\n[{i}/{len(episodes)}] 📄 {episode['title']}")
        
        result = await process_episode(episode, project_dir)
        
        if result:
            updated_episodes.append(result)
            success_count += 1
        else:
            # 保留原始信息，但标记失败
            episode['duration'] = 0
            updated_episodes.append(episode)
    
    # 更新 episodes.json
    data['episodes'] = updated_episodes
    with open(episodes_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"🎉 完成! 成功生成 {success_count}/{len(episodes)} 个音频")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
