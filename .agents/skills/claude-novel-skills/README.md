# Claude Novel Skills

> 小说创作系统——以**去耦合化的角色特点×情节元素**为核心方法，以**核心体验极端化**为质量导向。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skills-blueviolet)](https://claude.ai/code)

---

## 核心理念

### 去耦合化创作

**角色特点和情节元素是独立的维度，可以自由组合。**

```
角色表现 = 个性类型 × 情绪状态 × 行为动作 × 语言风格
章节内容 = 事件类型 × 事件风格 × 场景氛围 × 角色特点
```

同一角色在不同场景展现不同面——害羞时咬唇、愤怒时握拳、好奇时追问。角色不是脸谱，是多面体。

### 核心体验极端化

**好小说不是各维度都高分，而是某个维度做到极致。**

| 核心体验 | 极端化标准 |
|----------|-----------|
| 暧昧感 | 让读者脸红心跳，反复回味 |
| 诱惑力 | 让读者血脉贲张，欲罢不能 |
| 悲伤感 | 让读者泪流不止，久久不能释怀 |
| 笑点密度 | 让读者笑出声来，停不下来 |
| 悬念感 | 让读者猜不到结局，欲罢不能 |
| 热血感 | 让读者热血沸腾，握紧拳头 |
| 甜蜜度 | 让读者甜到牙疼，嘴角上扬 |
| 治愈感 | 让读者感到温暖，内心平静 |

---

## 工具集

| 目录 | 内容 | 用途 |
|------|------|------|
| `tools/techniques/` | 写作技法（模块A/B/C/D） | 创作方法论 |
| `tools/decoupled/` | 去耦合分类库 | 角色特点×情节元素 |

## 规则集

| 文件 | 内容 |
|------|------|
| `rules/output-rules.md` | 输出格式和文件系统规范 |
| `rules/quality-rules.md` | 七维度对比优化框架 |
| `rules/deslop-rules.md` | 去AI味（6 Gate + 三遍法） |
| `rules/check-rules.md` | 一致性和去耦合检查 |
| `rules/banned-words.md` | 禁用词表 |
| `rules/anti-ai-writing.md` | 反AI写作参考 |

---

## 目录结构

```
claude-novel-skills/
├── SKILL.md                        # skill入口（/novel）
├── CLAUDE.md                       # 项目指引文件
├── tools/
│   ├── techniques/                 # 写作技法
│   │   ├── module-a-character.md
│   │   ├── module-b-plot.md
│   │   ├── module-c-prose.md
│   │   └── module-d-antipatterns.md
│   └── decoupled/                  # 去耦合分类库
│       ├── character-traits.md
│       └── plot-elements.md
├── rules/                          # 规则集
│   ├── output-rules.md
│   ├── quality-rules.md
│   ├── deslop-rules.md
│   ├── banned-words.md
│   ├── anti-ai-writing.md
│   └── check-rules.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

## 使用

```bash
# 安装到 skill 目录
cp SKILL.md ~/.claude/skills/claude-novel-skills-main/SKILL.md
cp -r tools rules ~/.claude/skills/claude-novel-skills-main/
```

在 Claude Code 中调用：`/novel`、`/灵感`、`/大纲`、`/正文`、`/学习`

---

## License

[MIT](LICENSE)
