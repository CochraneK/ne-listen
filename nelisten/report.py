from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "—"))


def fmt_num(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"
    return "—"


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _percent(value: Any) -> str:
    parsed = _number(value)
    if parsed is None:
        return "—"
    v = parsed
    if 0 <= v <= 1:
        v *= 100
    return f"{v:.0f}%" if v.is_integer() else f"{v:.1f}%"


def _ranked(items: list[dict[str, Any]], value_key: str, limit: int = 6, suffix: str = "") -> str:
    rows = []
    for i, item in enumerate((items or [])[:limit], 1):
        rows.append(
            f'<li><span class="rank">{i:02d}</span><span class="rank-name">{esc(item.get("name"))}</span>'
            f'<span class="rank-value">{esc(fmt_num(item.get(value_key)))}{suffix}</span></li>'
        )
    return "".join(rows) or '<li class="empty">暂无数据</li>'


def _ratio_rows(items: list[dict[str, Any]], label_key: str, value_key: str, limit: int = 6) -> str:
    valid = []
    for item in (items or [])[:limit]:
        label, value = item.get(label_key), item.get(value_key)
        numeric = _number(value)
        if label is None or numeric is None:
            continue
        numeric = numeric * 100 if 0 <= numeric <= 1 else numeric
        valid.append((str(label), numeric))
    if not valid:
        return '<div class="empty">暂无数据</div>'
    max_value = max(v for _, v in valid) or 1
    out = []
    for label, value in valid:
        width = max(4, value / max_value * 100)
        shown = f"{value:.0f}%" if value.is_integer() else f"{value:.1f}%"
        out.append(
            f'<div class="ratio"><div class="ratio-line"><span>{esc(label)}</span><b>{shown}</b></div>'
            f'<div class="hairline"><i style="width:{width:.1f}%"></i></div></div>'
        )
    return "".join(out)


def _age_rows(items: list[dict[str, Any]], limit: int = 6) -> str:
    valid = []
    for item in (items or [])[:limit]:
        label, value = item.get("age"), item.get("playSongNum")
        numeric = _number(value)
        if label is None or numeric is None:
            continue
        valid.append((str(label), numeric))
    if not valid:
        return '<div class="empty">暂无数据</div>'
    max_value = max(v for _, v in valid) or 1
    return "".join(
        f'<div class="ratio"><div class="ratio-line"><span>{esc(label)}</span><b>{fmt_num(value)} 首</b></div>'
        f'<div class="hairline"><i style="width:{max(4, value/max_value*100):.1f}%"></i></div></div>'
        for label, value in valid
    )


def _year_strip(items: list[dict[str, Any]]) -> str:
    clean = []
    for x in items or []:
        year = x.get("year")
        plays = _number(x.get("playNum"))
        if year is not None and plays is not None:
            clean.append({"year": year, "plays": plays})
    clean.sort(key=lambda x: int(x["year"]))
    if not clean:
        return '<div class="empty">暂无年度足迹</div>'
    max_plays = max(float(x["plays"]) for x in clean) or 1
    cards = []
    for item in clean:
        height = max(8, float(item["plays"]) / max_plays * 100)
        cards.append(
            f'<div class="year"><div class="year-bar"><i style="height:{height:.1f}%"></i></div>'
            f'<b>{esc(item["year"])}</b><span>{fmt_num(item["plays"])}</span></div>'
        )
    return "".join(cards)


def _term_tags(items: list[dict[str, Any]], key: str = "term", limit: int = 12) -> str:
    terms = [str(item.get(key)) for item in (items or [])[:limit] if item.get(key)]
    return "".join(f'<span class="term">{esc(term)}</span>' for term in terms) or '<span class="empty">暂无文本结果</span>'


def _capability_list(coverage: dict[str, Any]) -> str:
    available = coverage.get("available") or []
    missing = coverage.get("missing") or []
    good = "".join(f'<span>✓ {esc(x)}</span>' for x in available)
    bad = "".join(f'<span class="muted">○ {esc(x)}</span>' for x in missing)
    return good + bad


def render(data: dict[str, Any], metrics: dict[str, Any], output: Path) -> None:
    s = metrics["summary"]
    idx = metrics["indices"]
    cov = metrics["coverage"]
    pf = metrics.get("providerFacts") or {}
    text_metrics = metrics.get("text") or {}
    deep_text = metrics.get("deepText") or {}
    network = metrics.get("network") or {}
    profile = data.get("profile") or {}
    collected = data.get("collectedAt") or "Unknown"

    month_song = (pf.get("monthTopSong") or {}).get("name")
    month_song_count = (pf.get("monthTopSong") or {}).get("playCount")
    month_artist = (pf.get("monthTopArtist") or {}).get("name")
    month_artist_count = (pf.get("monthTopArtist") or {}).get("playCount")
    style = pf.get("monthTopStyle") or {}
    year_items = pf.get("yearItems") or []
    year_count = len(year_items)
    years = [int(x.get("year")) for x in year_items if str(x.get("year", "")).isdigit()]
    year_span = f"{min(years)}—{max(years)}" if years else "持续记录"

    hero_title = f"最近，我一直在听《{month_song}》。" if month_song else "把听过的歌，留成一张长期的音乐地图。"
    nickname = profile.get("nickname") or "Local listener"

    display_date = str(collected)[:10] if collected else "—"
    overlap = (network.get("topOverlaps") or [None])[0]
    network_note = ""
    if overlap:
        network_note = f" 最相近的两个歌单是「{overlap.get('a')}」与「{overlap.get('b')}」，Jaccard {overlap.get('jaccard')}%。"

    text_section = ""
    if text_metrics.get("available"):
        drift = text_metrics.get("drift") or {}
        jsd = drift.get("jensenShannon")
        drift_text = f"{float(jsd):.3f}" if isinstance(jsd, (int, float)) else "—"
        semantic_distance = (deep_text.get("latent") or {}).get("centroidCosineDistance") if deep_text.get("available") else None
        semantic_text = f"{float(semantic_distance):.3f}" if isinstance(semantic_distance, (int, float)) else "—"
        agreement = deep_text.get("methodAgreementAMI")
        agreement_text = f"{float(agreement):.3f}" if isinstance(agreement, (int, float)) else "—"
        topic_html = ""
        if deep_text.get("available"):
            topic_html = "".join(
                f'<div class="topicrow"><span>{esc(topic.get("label"))}</span><b>{_percent(topic.get("prevalence"))}</b></div>'
                for topic in (deep_text.get("topics") or [])[:4]
            )
        text_section = f"""
<section id="lyrics"><div class="shell">
<div class="sectionhead"><h2>歌词里，也有一张地图。</h2><p>{fmt_num(text_metrics.get('songsWithLyrics'))}/{fmt_num(text_metrics.get('selectedSongs'))} 首歌词进入本次文本分析</p></div>
<div class="textmap">
<div><div class="subhead">BEHAVIOR-WEIGHTED TF-IDF</div><div class="termwall">{_term_tags(text_metrics.get('topTerms') or [])}</div><div class="subhead text-sub">EXPLORATORY NMF THEMES</div><div class="topiclist">{topic_html or '<div class="empty">深度主题层未启用</div>'}</div></div>
<div class="textaside"><div class="textfact"><span>词汇分布差异 · JSD</span><b>{drift_text}</b></div><div class="textfact"><span>潜在语义距离 · LSA</span><b>{semantic_text}</b></div><div class="textfact"><span>NMF ↔ LSA/KMeans 一致性 · AMI</span><b>{agreement_text}</b></div><div class="textfact"><span>最近更常出现</span><div class="termwall small">{_term_tags(drift.get('recentRisingTerms') or [], limit=8)}</div></div></div>
</div>
</div></section>
"""

    html_doc = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(nickname)} 的长期网易云听歌档案。">
<title>{esc(nickname)} · ne-listen</title>
<style>
:root{{--bg:#f4f0e9;--paper:#fffdf9;--ink:#282421;--muted:#776e66;--line:#dfd4c6;--accent:#b85d49;--soft:#eee4d7;--green:#7b8f75;--shadow:0 12px 36px rgba(48,39,31,.07)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"SF Pro Display","PingFang SC","Microsoft YaHei",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}a{{color:inherit}}.shell{{width:min(1120px,calc(100% - 32px));margin:auto}}
.nav{{position:sticky;top:0;z-index:20;background:rgba(244,240,233,.88);backdrop-filter:blur(16px);border-bottom:1px solid rgba(223,212,198,.8)}}.navin{{height:62px;display:flex;align-items:center;justify-content:space-between;gap:20px}}.brand{{font-weight:850;letter-spacing:-.035em}}.brand i{{font-style:normal;color:var(--accent)}}.links{{display:flex;gap:6px;align-items:center}}.links a{{text-decoration:none;font-size:12px;color:var(--muted);padding:8px 10px;border-radius:999px}}.links a:hover{{background:var(--paper);color:var(--ink)}}.links .gh{{border:1px solid var(--line);background:var(--paper)}}
.hero{{padding:96px 0 70px}}.eyebrow{{font-size:11px;letter-spacing:.16em;font-weight:850;color:var(--accent)}}h1{{font-size:clamp(52px,8vw,96px);line-height:.96;letter-spacing:-.075em;margin:14px 0 26px;max-width:1000px}}.hero-copy{{font-size:clamp(16px,2vw,20px);line-height:1.75;color:var(--muted);max-width:760px;margin:0}}.hero-copy strong{{color:var(--ink);font-weight:650}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:54px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.stat{{padding:22px 20px 22px 0}}.stat:not(:last-child){{border-right:1px solid var(--line);padding-right:20px;margin-right:20px}}.stat b{{display:block;font-size:30px;letter-spacing:-.05em}}.stat span{{font-size:11px;color:var(--muted)}}
section{{padding:78px 0;border-top:1px solid var(--line);scroll-margin-top:72px}}.sectionhead{{display:flex;align-items:end;justify-content:space-between;gap:30px;margin-bottom:34px}}.sectionhead h2{{font-size:clamp(32px,5vw,54px);line-height:1.02;letter-spacing:-.055em;margin:0;max-width:700px}}.sectionhead p{{max-width:440px;color:var(--muted);font-size:13px;line-height:1.7;margin:0}}
.now{{display:grid;grid-template-columns:1.35fr .65fr;gap:12px}}.feature{{background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:28px;box-shadow:var(--shadow)}}.feature-kicker{{font-size:10px;letter-spacing:.12em;color:var(--accent);font-weight:850}}.feature h3{{font-size:clamp(30px,4vw,54px);line-height:1.04;letter-spacing:-.055em;margin:18px 0 10px}}.feature p{{color:var(--muted);margin:0}}.facts{{display:grid;gap:0}}.fact{{padding:19px 0;border-bottom:1px solid var(--line)}}.fact:first-child{{padding-top:0}}.fact:last-child{{border-bottom:0;padding-bottom:0}}.fact span{{display:block;font-size:11px;color:var(--muted)}}.fact b{{font-size:21px;letter-spacing:-.025em}}
.duo{{display:grid;grid-template-columns:1fr 1fr;gap:46px}}.ranklist{{list-style:none;padding:0;margin:0}}.ranklist li{{display:grid;grid-template-columns:34px 1fr auto;gap:12px;align-items:baseline;padding:14px 0;border-bottom:1px solid var(--line)}}.ranklist li:last-child{{border-bottom:0}}.rank{{font-size:10px;color:var(--accent);font-weight:850}}.rank-name{{font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.rank-value{{font-size:12px;color:var(--muted)}}.subhead{{font-size:11px;letter-spacing:.12em;color:var(--muted);font-weight:800;margin:0 0 8px}}
.taste{{display:grid;grid-template-columns:repeat(3,1fr);gap:34px}}.taste h3{{font-size:18px;margin:0 0 20px}}.ratio{{margin:15px 0}}.ratio-line{{display:flex;justify-content:space-between;gap:14px;font-size:13px}}.ratio-line b{{font-size:12px;color:var(--muted)}}.hairline{{height:2px;background:#e4dbcf;margin-top:8px;overflow:hidden}}.hairline i{{display:block;height:100%;background:var(--accent)}}.yearstrip{{height:230px;display:grid;grid-template-columns:repeat({max(1, year_count)},minmax(54px,1fr));gap:9px;align-items:end}}.year{{display:grid;grid-template-rows:1fr auto auto;min-width:0;text-align:center;gap:6px;height:100%}}.year-bar{{height:165px;display:flex;align-items:end;justify-content:center;border-bottom:1px solid var(--line)}}.year-bar i{{display:block;width:min(28px,60%);background:var(--accent);border-radius:5px 5px 0 0;opacity:.86}}.year b{{font-size:12px}}.year span{{font-size:10px;color:var(--muted)}}
.patterns{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.pattern{{padding:26px 28px 26px 0}}.pattern:not(:last-child){{border-right:1px solid var(--line);padding-right:28px;margin-right:28px}}.pattern b{{font-size:35px;letter-spacing:-.05em;display:block}}.pattern span{{font-size:13px;font-weight:700}}.pattern p{{font-size:11px;line-height:1.6;color:var(--muted);margin:6px 0 0}}
.textmap{{display:grid;grid-template-columns:1.25fr .75fr;gap:46px;align-items:start}}.text-sub{{margin-top:32px}}.topiclist{{margin-top:10px;border-top:1px solid var(--line)}}.topicrow{{display:flex;justify-content:space-between;gap:18px;padding:11px 0;border-bottom:1px solid var(--line);font-size:13px}}.topicrow span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.topicrow b{{font-size:11px;color:var(--muted);white-space:nowrap}}.termwall{{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}}.term{{display:inline-flex;padding:9px 13px;border-radius:999px;background:var(--paper);border:1px solid var(--line);font-size:14px;box-shadow:var(--shadow)}}.termwall.small .term{{font-size:11px;padding:6px 9px;box-shadow:none}}.textaside{{border-left:1px solid var(--line);padding-left:32px}}.textfact{{padding:0 0 20px;margin-bottom:20px;border-bottom:1px solid var(--line)}}.textfact:last-child{{border-bottom:0;margin-bottom:0}}.textfact>span{{display:block;font-size:11px;color:var(--muted);margin-bottom:7px}}.textfact>b{{font-size:30px;letter-spacing:-.04em}}.playlists{{display:grid;grid-template-columns:1.1fr .9fr;gap:46px}}.library-note{{font-size:clamp(28px,4vw,44px);line-height:1.08;letter-spacing:-.045em;margin:0 0 18px}}.library-copy{{color:var(--muted);max-width:460px}}.mini-stats{{display:flex;gap:26px;margin-top:28px;flex-wrap:wrap}}.mini-stats b{{font-size:22px;display:block}}.mini-stats span{{font-size:10px;color:var(--muted)}}
details{{border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}summary{{cursor:pointer;list-style:none;padding:22px 0;font-weight:750}}summary::-webkit-details-marker{{display:none}}summary:after{{content:"＋";float:right;color:var(--muted)}}details[open] summary:after{{content:"－"}}.method{{padding:0 0 26px;color:var(--muted);font-size:12px;line-height:1.75;display:grid;grid-template-columns:1fr 1fr;gap:28px}}.method strong{{color:var(--ink)}}.caps{{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}}.caps span{{border:1px solid var(--line);background:var(--paper);border-radius:999px;padding:4px 8px;font-size:10px;color:var(--green)}}.caps .muted{{color:var(--muted)}}.empty{{color:var(--muted);font-size:12px;padding:10px 0}}
.footer{{padding:40px 0 64px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:24px;color:var(--muted);font-size:11px}}
@media(max-width:900px){{.now,.playlists,.textmap{{grid-template-columns:1fr}}.textaside{{border-left:0;border-top:1px solid var(--line);padding:24px 0 0}}.taste{{grid-template-columns:1fr 1fr}}.duo{{gap:24px}}.stats{{grid-template-columns:repeat(2,1fr)}}.stat:nth-child(2){{border-right:0;margin-right:0}}.stat:nth-child(-n+2){{border-bottom:1px solid var(--line)}}.yearstrip{{overflow-x:auto;grid-template-columns:repeat({max(1, year_count)},72px)}}}}
@media(max-width:650px){{.shell{{width:min(100% - 22px,1120px)}}.hero{{padding:66px 0 54px}}.links a:not(.gh){{display:none}}.sectionhead{{display:block}}.sectionhead p{{margin-top:12px}}.duo,.taste,.patterns,.method{{grid-template-columns:1fr}}.duo{{gap:44px}}.patterns{{border-bottom:0}}.pattern,.pattern:not(:last-child){{border-right:0;border-bottom:1px solid var(--line);padding:20px 0;margin:0}}.stats{{display:grid;grid-template-columns:1fr 1fr}}.stat,.stat:not(:last-child){{margin:0;padding:18px 14px 18px 0}}.stat:nth-child(odd){{border-right:1px solid var(--line)}}.stat b{{font-size:24px}}.feature{{padding:22px}}.yearstrip{{height:auto;overflow:visible;grid-template-columns:repeat(3,1fr);gap:18px 8px}}.year{{height:128px}}.year-bar{{height:86px}}.footer{{display:block}}.footer span{{display:block;margin-top:8px}}}}
</style>
</head>
<body>
<nav class="nav"><div class="shell navin"><div class="brand">ne-<i>listen</i></div><div class="links"><a href="#now">最近</a><a href="#long">长期</a><a href="#taste">版图</a><a href="#years">年份</a><a class="gh" href="https://github.com/CochraneK/ne-listen">GitHub ↗</a></div></div></nav>
<main>
<header class="shell hero">
<div class="eyebrow">A PERSONAL LISTENING ARCHIVE</div>
<h1>{esc(hero_title)}</h1>
<p class="hero-copy">这是 <strong>{esc(nickname)}</strong> 的长期听歌档案。一份会继续生长的音乐记录。</p>
<div class="stats">
<div class="stat"><b>{fmt_num(s.get('providerListenSongs'))}</b><span>网易云听歌记录</span></div>
<div class="stat"><b>{fmt_num(s.get('likedIds'))}</b><span>红心歌曲</span></div>
<div class="stat"><b>{fmt_num(s.get('playlists'))}</b><span>歌单</span></div>
<div class="stat"><b>{fmt_num(year_count)}</b><span>年有记录</span></div>
</div>
</header>

<section id="now"><div class="shell">
<div class="sectionhead"><h2>最近在听</h2><p>本月最常出现的声音。</p></div>
<div class="now">
<article class="feature"><div class="feature-kicker">THIS MONTH</div><h3>{esc(month_song)}</h3><p>{fmt_num(month_song_count)} 次 · 网易云本月足迹</p></article>
<aside class="feature facts">
<div class="fact"><span>最近常听的歌手</span><b>{esc(month_artist)}</b><small>{fmt_num(month_artist_count)} 次</small></div>
<div class="fact"><span>网易云突出曲风</span><b>{esc(style.get('genre'))}</b><small>{esc(style.get('secondGenre'))}</small></div>
<div class="fact"><span>本月听歌天数</span><b>{fmt_num(pf.get('monthListenDays'))} 天</b></div>
</aside>
</div>
</div></section>

<section id="long"><div class="shell">
<div class="sectionhead"><h2>有些声音，会一直回来。</h2></div>
<div class="duo">
<div><div class="subhead">SONGS I RETURN TO</div><ol class="ranklist">{_ranked(metrics.get('topSongs') or [], 'playCount', 6)}</ol></div>
<div><div class="subhead">ARTISTS I RETURN TO</div><ol class="ranklist">{_ranked(metrics.get('topArtists') or [], 'playCount', 6)}</ol></div>
</div>
</div></section>

<section id="taste"><div class="shell">
<div class="sectionhead"><h2>我的音乐版图，不止一个标签。</h2><p>曲风 · 语言 · 年代</p></div>
<div class="taste">
<div><h3>曲风</h3>{_ratio_rows(pf.get('stylePreferences') or [], 'tagName', 'ratio')}</div>
<div><h3>语言</h3>{_ratio_rows(pf.get('monthLanguageDistribution') or [], 'language', 'percent')}</div>
<div><h3>年代</h3>{_age_rows(pf.get('monthAgeDistribution') or [])}</div>
</div>
</div></section>

{text_section}

<section id="years"><div class="shell">
<div class="sectionhead"><h2>听歌这件事，已经留下了年份。</h2><p>{esc(year_span)}</p></div>
<div class="yearstrip">{_year_strip(year_items)}</div>
</div></section>

<section><div class="shell">
<div class="sectionhead"><h2>再看三件小事。</h2></div>
<div class="patterns">
<div class="pattern"><b>{_percent(idx.get('repeatIndex'))}</b><span>Repeat Index</span><p>长期 Top100 中，头部 10% 歌曲占已知播放的比例。</p></div>
<div class="pattern"><b>{fmt_num(idx.get('tasteDiversityEffectiveArtists'))}</b><span>Effective artists</span><p>基于 Shannon entropy 的有效歌手数量。</p></div>
<div class="pattern"><b>{_percent(idx.get('recentOutsideTop100'))}</b><span>最近不在 Top100</span><p>不是“新歌率”，只说明最近播放没有落在长期 Top100。</p></div>
</div>
</div></section>

<section id="library"><div class="shell">
<div class="sectionhead"><h2>歌单，是另一种记忆。</h2></div>
<div class="playlists">
<div><h3 class="library-note">{fmt_num(s.get('likedIds'))} 首红心，{fmt_num(s.get('playlistKnownTracks'))} 首可恢复歌单曲目。</h3><p class="library-copy">首页只留几个最大的歌单，完整内容保留在私有数据层。{esc(network_note)}</p><div class="mini-stats"><div><b>{fmt_num(s.get('createdPlaylists'))}</b><span>自建歌单</span></div><div><b>{fmt_num(s.get('subscribedPlaylists'))}</b><span>收藏歌单</span></div><div><b>{_percent(s.get('playlistTrackCoverage'))}</b><span>曲目恢复率</span></div></div></div>
<div><div class="subhead">LARGEST PLAYLISTS</div><ol class="ranklist">{_ranked(metrics.get('topPlaylists') or [], 'trackCount', 6, ' 首')}</ol></div>
</div>
</div></section>

<section><div class="shell">
<details>
<summary>数据说明</summary>
<div class="method">
<div><strong>这页是什么</strong><br>网易云直接返回的数据 + ne-listen 的确定性计算。歌词文本只在私有构建层处理，公开页不包含歌词原文；NMF/LSA 只发布聚合主题和距离；当前 NMF 与 LSA/KMeans 的 AMI 会直接展示，用来提醒主题的一致性有限。长期排行接口只覆盖 Top100，因此页面不会把榜外历史当作 0，也不会声称恢复了每一次播放。</div>
<div><strong>当前覆盖</strong><br>{fmt_num(cov.get('score'))}% 的 V1 数据能力在本次同步中可用。Cookie、原始 API 响应、normalized archive 和 snapshots 都不会进入公开 Page。<div class="caps">{_capability_list(cov)}</div></div>
</div>
</details>
</div></section>
</main>
<footer class="shell footer"><div>ne-listen · personal music archive</div><span>Last snapshot · {esc(display_date)}</span></footer>
</body>
</html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_doc, encoding="utf-8")
