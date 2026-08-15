---
name: no-autonomous-git-commit
description: 只有用户明确说"提交/上传"时才 git commit/push，绝不自主提交
metadata:
  type: feedback
---

只有用户在本轮指令里明确说出「提交」「上传」「commit」「push」等词，才执行 `git add` / `git commit` / `git push`。否则绝不自主提交。

**Why:** 用户对版本历史有强控制欲。写作项目里大量改动是草稿/试验/中间态，自主提交会污染提交历史、打乱用户的版本节奏；用户希望自己决定"哪些改动值得进历史、什么时候进"。

**How to apply:** 每次想提交前，回看用户最近一条消息是否明确要求提交。没有就只做文件修改，把提交决定留给用户。即使改动"看起来该提交了"也不提交，等用户发话。此规则与 [[project-state-and-decisions]]、[[novel-tracking-update-rule]] 并行——更新追踪文件 ≠ 可以提交。
