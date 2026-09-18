<div align="center">

# ne-listen

**把网易云“听过什么”变成一份可长期积累、可验证、可重建的个人听歌档案。**

`collect → archive → normalize → analyze → report`

</div>

`ne-listen` 是一个 **local-first** 的网易云音乐个人数据提取、长期快照、统计分析与 HTML 报告生成器。

它不是播放器，也不下载音乐；它只做一件事：**尽可能忠实地保存网易云当前能提供的个人听歌数据，并据此生成一份漂亮、可解释的报告。**

## 设计原则

1. **原始事实优先**：API 返回内容原样归档，标准化数据另存。
2. **unknown ≠ 0**：接口没给出的历史，不会被当成“没有发生”。
3. **Observed / Derived / Estimated 分层**：报告告诉你每个指标从哪来。
4. **Snapshot-first**：每次同步都保存快照，越用越像自己的长期音乐数据库。
5. **Adapter 可替换**：不把项目绑定到某一个逆向 API 实现。
6. **隐私默认安全**：Cookie、raw、snapshot 不进 Git；公开 Page 只发布派生报告。

## 真实网易云 Page

仓库支持和 `we-read` 类似的真实个人档案模式，而且不需要把 Cookie 发到聊天或提交到 Git。

### 第一次启用

1. 打开仓库 `Settings → Pages`，在 **Build and deployment → Source** 选择 **GitHub Actions**。
2. 打开 `Settings → Secrets and variables → Actions`，新建 repository secret：

```text
Name: NETEASE_MUSIC_U
Value: 只填 MUSIC_U= 后面的值
```

然后到 `Actions → Build listening archive → Run workflow` 手动运行一次。

> `MUSIC_U` 是登录凭据。不要提交到 Git、Issue、截图或聊天；只存进 GitHub Actions Secret 或本地环境变量。

Workflow：

```text
GitHub Secret
→ ephemeral GitHub runner
→ localhost NetEase API backend
→ ne-listen read-only collector
→ temporary raw / normalized data
→ metrics
→ static HTML report
→ GitHub Pages artifact
```

不会上传到 Page：`MUSIC_U`、完整 Cookie、raw API response、snapshot、normalized JSON。Page 只包含派生的报告 HTML 与聚合后的 `metrics.json`。

### 当前报告章节

- 生涯概览：已知播放、长期排行歌曲、红心数、歌单数、账户等级 / listenSongs；
- How you listen：Repeat Index、Artist Loyalty、Taste Diversity、Exploration Proxy；
- 长期偏好：Top songs / artists / albums；
- Current rotation：本周歌曲与歌手；
- Taste map：发行年代、Hidden Favorites；
- Library：自建 / 收藏歌单、歌单曲目覆盖；
- Data coverage：明确哪些网易云来源本次真正拿到了。

> 网易云的“所有时间听歌排行”并不等于逐次、完整的终身播放日志。ne-listen 不把不可恢复的历史伪造成精确时间线。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

连接本地兼容 API：

```bash
export NELISTEN_API_BASE=http://127.0.0.1:3000
export NELISTEN_COOKIE='MUSIC_U=...'
ne-listen sync
```

## 安全边界

- 不提交 `MUSIC_U`、Cookie 或二维码登录凭据。
- 不提交 `data/raw/`、`data/snapshots/`、`data/normalized/`。
- 不调用下载/解灰接口。
- 不执行点赞、收藏、评论、歌单编辑等远端写操作。
- 默认只读。

## 开发

```bash
python -m unittest discover -s tests -v
```
