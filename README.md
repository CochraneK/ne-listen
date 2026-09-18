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
4. **Snapshot-first**：本地同步保存完整私有快照；GitHub Actions 的私有工作目录是临时的，因此公开 Page 额外持久化一份不含原始歌词/播放明细的 **聚合历史 history.json**，用于后续纵向变化。
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

### 当前分析层

- **Listening behavior**：Repeat Index、Artist Loyalty、Taste Diversity、长期 Top100 与最近播放；
- **Native footprint**：网易云周/月/年足迹、曲风、语言、年代与听歌时段；
- **Lyric text mining**：私有歌词语料、行为加权 TF-IDF、词汇结构、语言脚本、长期↔近期 JSD；
- **Deep text**：NMF 主题、LSA 潜在语义距离、KMeans 对照、AMI 方法一致性；
- **Playlist network**：歌单 Jaccard 重叠、网络组件、跨歌单桥梁歌手；
- **Longitudinal history**：公开保存不含歌词/明细的日级聚合 `history.json`，为后续 taste drift / change-point 做准备；
- **Evidence layer**：unknown ≠ 0；长期排行只按网易云当前可见 Top100 解释。

详见 `docs/ANALYSIS.md` 与 `docs/TEXT_MINING.md`。

> 网易云的“所有时间听歌排行”并不等于逐次、完整的终身播放日志。ne-listen 不把不可恢复的历史伪造成精确时间线。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[deep]'
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
