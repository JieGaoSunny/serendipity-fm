import json

# 读取现有数据
with open('data/episodes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修复作者名称重复
for ep in data['episodes']:
    author = ep.get('author', '')
    if len(author) > 2:
        half = len(author) // 2
        if author[:half] == author[half:]:
            old = author
            ep['author'] = author[:half]
            print(f'修复: {old} -> {ep["author"]}')

# 保存
with open('data/episodes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('\n✅ 作者名称已修复')
