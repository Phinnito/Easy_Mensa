# Easy_Mensa 🐱

这是“小猫食堂 / Chaetzli”的菜谱网站。

目标很简单：打开网页以后就能看菜单、看食材、看替代方案，或者让系统根据家里现有的食材推荐今天可以做什么。

## 🐱 怎么打开小猫食堂

### 最简单的方法：直接打开网页

小猫食堂的固定网址计划为：

```text
https://phinnito.github.io/Easy_Mensa/
```

只要 GitHub Pages 已经启用，这个网址在普通浏览器里直接打开即可。

不需要安装 Python，不需要打开 GitHub Codespaces，也不需要运行 Streamlit。

可以直接把这个网址：

- 收藏到浏览器书签
- 放到 Mac Dock
- 添加到手机主屏幕
- 发给需要使用小猫食堂的人

以后黄师傅新增、编辑或删除菜单后，网页会自动更新。

---

## 💻 在自己的 Mac 上一键打开

如果希望在 Terminal 里输入一个命令直接打开，可以先安装一次：

```bash
gh api -H "Accept: application/vnd.github.raw+json" \
  repos/Phinnito/Easy_Mensa/contents/install_commands.sh \
  | bash

source ~/.zshrc
```

以后只需要输入：

```bash
Chaetzli
```

它会直接打开小猫食堂网页。

普通使用者其实不需要这一步，直接保存网页书签更简单。

---

## 🍽️ 小猫食堂里可以做什么

目前前台包含：

### 📖 所有菜单

浏览已经发布的菜谱，可以查看：

- 菜名
- 菜系
- 制作时间
- 难度
- 份数
- 食材
- 替换食材
- 完整步骤
- 黄师傅提醒

### 🥬 我有什么

选择家里现在有的食材以后，小猫食堂会判断：

- 🟢 很适合做
- 🟡 可以做，需要替换食材
- 🟠 可以做，但味道会有变化
- 🔴 缺少必要食材

系统不只是简单计算“有几个食材”，还会考虑：

- 必须有
- 最好有
- 可选
- 替代食材
- 替代后味道变化程度

### 🎲 Roll 菜谱

不知道吃什么时，可以按照场景随机选择一道菜，例如：

- 聚会菜谱
- 精致一人食
- 随便吃点
- 两个人吃
- 认真做饭

---

## 🌐 如果网页还不能直接打开

如果打开下面的网址：

```text
https://phinnito.github.io/Easy_Mensa/
```

还没有出现小猫食堂，需要确认 GitHub Pages 已启用。

进入仓库：

```text
Settings → Pages
```

然后在 **Build and deployment** 中把 **Source** 设置为：

```text
GitHub Actions
```

如果当前 GitHub 套餐不允许 Private repository 使用 Pages，也可以把仓库改成 Public：

```text
Settings
→ General
→ Danger Zone
→ Change repository visibility
→ Make public
```

改成 Public 后，仓库代码和菜谱数据会公开可见，但不会公开你的 GitHub 密码，也不会公开本地 SSH key。

---

## 👨‍🍳 黄师傅后台

黄师傅后台用于管理菜单，包括：

- 新增菜单
- 查看菜单列表
- 编辑菜单
- 删除重复或错误菜单

Mac Terminal 中输入：

```bash
ChefHuang
```

即可打开后台。

后台保留为受保护入口，因为它具有修改和删除菜单、写回 GitHub 的能力。

---

## 📁 数据结构

每道菜保存为一个 JSON：

```text
data/recipes/
```

菜品图片位于：

```text
images/recipes/
```

静态小猫食堂页面位于：

```text
site/
```

每次菜单数据发生变化后，GitHub Actions 会重新生成并发布小猫食堂。
