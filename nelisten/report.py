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


def _bars(items: list[dict[str, Any]], value_key: str, suffix: str = "") -> str:
    if not items:
        return '<div class="empty">No observed data yet.</div>'
    max_v = max(float(x.get(value_key) or 0) for x in items) or 1
    rows = []
    for i, item in enumerate(items, 1):
        v = float(item.get(value_key) or 0)
        width = max(2, v / max_v * 100)
        liked = " ♥" if item.get("liked") else ""
        note = " · subscribed" if item.get("subscribed") else ""
        rows.append(
            f'''<div class="bar-row"><div class="rank">{i:02d}</div><div class="bar-main"><div class="bar-label"><span>{esc(item.get("name"))}{liked}{note}</span><b>{esc(fmt_num(v))}{suffix}</b></div><div class="track"><div class="fill" style="width:{width:.1f}%"></div></div></div></div>'''
        )
    return "".join(rows)


def _decade_bars(items: list[dict[str, Any]]) -> str:
    adapted = [{"name": x.get("name"), "count": x.get("count")} for x in items]
    return _bars(adapted, "count")


def _fact_rows(items: list[dict[str, Any]], label_key: str, value_key: str, suffix: str = "") -> str:
    rows = []
    for item in items or []:
        label = item.get(label_key)
        value = item.get(value_key)
        if label is None or value is None:
            continue
        rows.append(f'<div class="fact-row"><span>{esc(label)}</span><b>{esc(value)}{suffix}</b></div>')
    return "".join(rows) or '<div class="empty">No observed data yet.</div>'


def _provider_badges(data: dict[str, Any]) -> str:
    caps = data.get("capabilities") or {}
    groups = [
        ("长期排行", ["record_all"]),
        ("本周排行", ["record_week"]),
        ("最近播放", ["recent_songs", "recent_listen"]),
        ("听歌时长", ["listen_total", "listen_realtime_week", "listen_realtime_month"]),
        ("年度足迹", ["listen_year", "listen_report_year"]),
        ("曲风偏好", ["style_preference"]),
        ("歌单曲目", ["playlist_tracks"]),
    ]
    out = []
    for label, keys in groups:
        ok = any(caps.get(k) for k in keys)
        out.append(f'<span class="source {"on" if ok else "off"}">{"●" if ok else "○"} {esc(label)}</span>')
    return "".join(out)


def render(data: dict[str, Any], metrics: dict[str, Any], output: Path) -> None:
    s = metrics["summary"]
    idx = metrics["indices"]
    cov = metrics["coverage"]
    pf = metrics.get("providerFacts") or {}
    profile = data.get("profile") or {}
    collected = data.get("collectedAt") or "Unknown"
    raw_json = json.dumps({"schemaVersion": data.get("schemaVersion"), "coverage": cov}, ensure_ascii=False)

    def metric_card(label: str, value: Any, note: str, kind: str = "Derived") -> str:
        v = "—" if value is None else value
        return f'''<article class="metric"><div class="tag">{kind}</div><div class="metric-value">{esc(v)}</div><div class="metric-label">{esc(label)}</div><p>{esc(note)}</p></article>'''

    html_doc = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ne-listen · Listening Archive</title>
<style>
:root{{--bg:#0b0d12;--panel:#121722;--panel2:#171d2a;--text:#eef2f7;--muted:#97a0af;--line:#262e3e;--accent:#ff5b67;--accent2:#ff9c6b;--good:#69d6a3;--shadow:0 18px 50px rgba(0,0,0,.22)}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:radial-gradient(900px 500px at 80% -10%,rgba(255,91,103,.14),transparent 60%),var(--bg);color:var(--text);font:15px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
a{{color:inherit}} .shell{{max-width:1180px;margin:auto;padding:28px 22px 80px}} .nav{{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;margin:-28px -22px 54px;padding:18px 22px;background:rgba(11,13,18,.84);backdrop-filter:blur(16px);border-bottom:1px solid rgba(38,46,62,.7)}} .brand{{font-weight:850;letter-spacing:-.03em}} .navlinks{{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}} .pill,.navlinks a{{border:1px solid var(--line);padding:6px 10px;border-radius:999px;color:var(--muted);font-size:11px;text-decoration:none}}
.hero{{display:grid;grid-template-columns:1.5fr .8fr;gap:24px;align-items:end;margin-bottom:28px}} h1{{font-size:clamp(44px,8vw,94px);line-height:.93;letter-spacing:-.065em;margin:0 0 22px;max-width:850px}} .lead{{font-size:18px;color:var(--muted);max-width:720px}} .identity{{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:26px;padding:24px;box-shadow:var(--shadow)}} .identity small{{color:var(--muted)}} .identity strong{{display:block;font-size:24px;margin-top:4px}} .source-row{{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}} .source{{font-size:11px;border:1px solid var(--line);padding:5px 8px;border-radius:999px}} .source.on{{color:var(--good)}} .source.off{{color:#697384}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}} .stat,.metric,.panel{{border:1px solid var(--line);background:rgba(18,23,34,.88);border-radius:22px}} .stat{{padding:22px}} .stat b{{font-size:32px;letter-spacing:-.04em;display:block}} .stat span{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}} .stat small{{display:block;color:#697384;margin-top:6px}}
.section{{margin-top:54px;scroll-margin-top:90px}} .section-head{{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:17px}} h2{{font-size:30px;letter-spacing:-.04em;margin:0}} .section-head p{{margin:0;color:var(--muted);max-width:560px;text-align:right}} .metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}} .metric{{padding:20px;min-height:180px}} .tag{{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:3px 8px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}} .metric-value{{font-size:36px;font-weight:800;letter-spacing:-.04em;margin-top:16px}} .metric-label{{font-weight:700}} .metric p{{color:var(--muted);font-size:12px;margin:8px 0 0}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} .three{{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:16px}} .panel{{padding:24px;overflow:hidden}} .panel h3{{font-size:18px;margin:0 0 5px}} .panel .sub{{color:var(--muted);font-size:12px;margin:0 0 18px}} .bar-row{{display:flex;gap:12px;align-items:center;margin:13px 0}} .rank{{font-size:11px;color:#657084;width:22px}} .bar-main{{flex:1;min-width:0}} .bar-label{{display:flex;justify-content:space-between;gap:12px;font-size:13px}} .bar-label span{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .bar-label b{{font-size:12px;color:var(--muted)}} .track{{height:5px;background:#232b39;border-radius:999px;margin-top:6px;overflow:hidden}} .fill{{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:999px}} .empty{{padding:30px 0;color:var(--muted)}} .fact-row{{display:flex;justify-content:space-between;gap:14px;padding:10px 0;border-bottom:1px solid rgba(38,46,62,.65);font-size:13px}} .fact-row:last-child{{border-bottom:0}} .fact-row span{{color:var(--muted)}} .fact-row b{{text-align:right}}
.story{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .story-card{{padding:24px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,rgba(255,91,103,.09),rgba(18,23,34,.92))}} .story-card b{{display:block;font-size:25px;letter-spacing:-.03em;margin-bottom:6px}} .story-card p{{margin:0;color:var(--muted)}}
.coverage{{display:grid;grid-template-columns:220px 1fr;gap:26px;align-items:center}} .ring{{width:180px;aspect-ratio:1;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--good) 0 {cov['score']}%,#252c38 {cov['score']}% 100%);position:relative}} .ring:after{{content:"";position:absolute;inset:14px;background:var(--panel);border-radius:50%}} .ring b{{font-size:38px;z-index:1}} .caps{{display:grid;grid-template-columns:1fr 1fr;gap:8px}} .cap{{padding:10px 12px;border-radius:12px;background:#171d28;font-size:12px}} .yes{{color:var(--good)}} .no{{color:#7d8795}} footer{{margin-top:60px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:22px}}
@media(max-width:950px){{.hero,.two,.three,.coverage{{grid-template-columns:1fr}} .grid,.metrics{{grid-template-columns:repeat(2,1fr)}} .section-head{{align-items:start;flex-direction:column}} .section-head p{{text-align:left}}}} @media(max-width:560px){{.grid,.metrics,.caps,.story{{grid-template-columns:1fr}} .shell{{padding:20px 14px 60px}} .nav{{margin:-20px -14px 42px;padding:14px}} .navlinks a:nth-child(n+4){{display:none}}}}
</style></head><body><main class="shell">
<div class="nav"><div class="brand">ne-listen</div><div class="navlinks"><a href="#life">生涯</a><a href="#now">最近</a><a href="#taste">偏好</a><a href="#library">歌单</a><a href="#coverage">数据边界</a></div></div>
<section class="hero"><div><h1>Your listening life, reconstructed.</h1><p class="lead">像阅读档案一样，把网易云从一次性的年度总结变成持续积累的个人听歌档案。这里区分 API 直接观测、代码派生和仍然未知的历史。</p><div class="source-row">{_provider_badges(data)}</div></div><div class="identity"><small>Listening archive for</small><strong>{esc(profile.get('nickname') or 'Local listener')}</strong><small>snapshot · {esc(collected)}</small></div></section>
<section class="grid" id="life">
<div class="stat"><b>{fmt_num(s['knownPlays'])}</b><span>known plays</span><small>来自当前可见长期排行，不宣称等于历史总播放</small></div>
<div class="stat"><b>{fmt_num(s['uniqueSongs'])}</b><span>ranked songs</span><small>长期排行中已观测歌曲</small></div>
<div class="stat"><b>{fmt_num(s['likedIds'])}</b><span>liked songs</span><small>当前红心 ID 数</small></div>
<div class="stat"><b>{fmt_num(s['playlists'])}</b><span>playlists</span><small>{fmt_num(s['createdPlaylists'])} created · {fmt_num(s['subscribedPlaylists'])} subscribed</small></div>
</section>
<section class="section"><div class="section-head"><div><div class="pill">Life archive</div><h2>你的音乐生涯，目前能确认什么</h2></div><p>账户层指标和长期排行是两种不同证据。网易云没有返回的完整历史不会被补成 0。</p></div><div class="story">
<div class="story-card"><b>Lv.{esc(s['accountLevel']) if s['accountLevel'] is not None else '—'}</b><p>网易云账户等级。若接口没有返回则保持未知。</p></div>
<div class="story-card"><b>{fmt_num(s['providerListenSongs'])}</b><p>用户详情接口中的 listenSongs（若可用），与本页“known plays”不是同一口径。</p></div>
<div class="story-card"><b>{fmt_num(s['playlistKnownTracks'])}</b><p>本次从可访问歌单中实际恢复出的唯一曲目。</p></div>
<div class="story-card"><b>{fmt_num(s['accountAgeDays'])} days</b><p>若网易云返回 createDays，这里展示账户存在时长。</p></div>
</div></section>
<section class="section"><div class="section-head"><div><div class="pill">Derived layer</div><h2>How you listen</h2></div><p>这些指标描述已观测播放分布，不等同于人格判断；以后 snapshot 累积后会加入真正的纵向变化。</p></div><div class="metrics">
{metric_card('Repeat Index', f"{idx['repeatIndex']}%" if idx['repeatIndex'] is not None else None, 'Top 10% 歌曲占已知播放量的比例。')}
{metric_card('Artist Loyalty', f"{idx['artistLoyalty']}%" if idx['artistLoyalty'] is not None else None, 'Top 10% 歌手占已知播放量的比例。')}
{metric_card('Taste Diversity', idx['tasteDiversityEffectiveArtists'], '基于 Shannon entropy 的有效歌手数量。')}
{metric_card('Exploration Proxy', f"{idx['explorationProxy']}%" if idx['explorationProxy'] is not None else None, '最近播放中，历史播放≤2次歌曲的比例。')}
</div></section>
<section class="section two"><div class="panel"><h3>Most played songs</h3><p class="sub">当前“所有时间排行”接口能观测到的高频歌曲。</p>{_bars(metrics['topSongs'],'playCount')}</div><div class="panel"><h3>Artists you return to</h3><p class="sub">多歌手歌曲按歌手平分一次播放权重。</p>{_bars(metrics['topArtists'],'playCount')}</div></section>
<section class="section" id="now"><div class="section-head"><div><div class="pill">Current rotation</div><h2>最近这一周，你在回到什么</h2></div><p>把长期偏好和短期循环分开看，避免把“这周突然上头”误当作长期口味。</p></div><div class="two"><div class="panel"><h3>Week songs</h3>{_bars(metrics['weekSongs'],'playCount')}</div><div class="panel"><h3>Week artists</h3>{_bars(metrics['weekArtists'],'playCount')}</div></div></section>
<section class="section" id="native"><div class="section-head"><div><div class="pill">Observed · NetEase native</div><h2>网易云自己的听歌足迹</h2></div><p>这一层不是 ne-listen 猜的，而是网易云当前听歌足迹接口直接返回。和长期 Top100 派生指标分开呈现。</p></div>
<div class="grid">
<div class="stat"><b>{esc((pf.get('monthTopSong') or {}).get('name'))}</b><span>month top song</span><small>{fmt_num((pf.get('monthTopSong') or {}).get('playCount'))} plays</small></div>
<div class="stat"><b>{esc((pf.get('monthTopArtist') or {}).get('name'))}</b><span>month top artist</span><small>{fmt_num((pf.get('monthTopArtist') or {}).get('playCount'))} plays</small></div>
<div class="stat"><b>{esc((pf.get('monthTopStyle') or {}).get('genre'))}</b><span>month top style</span><small>{esc((pf.get('monthTopStyle') or {}).get('secondGenre'))}</small></div>
<div class="stat"><b>{fmt_num(pf.get('monthListenDays'))}</b><span>listening days</span><small>current month · provider observed</small></div>
</div>
<div class="three" style="margin-top:16px">
<div class="panel"><h3>Style preference</h3><p class="sub">网易云曲风偏好接口返回的标签比例。</p>{_fact_rows(pf.get('stylePreferences') or [], 'tagName', 'ratio')}</div>
<div class="panel"><h3>Language mix</h3><p class="sub">当前月度足迹中的语言结构。</p>{_fact_rows(pf.get('monthLanguageDistribution') or [], 'language', 'percent')}</div>
<div class="panel"><h3>Music age</h3><p class="sub">当前月度足迹中的发行年代结构。</p>{_fact_rows(pf.get('monthAgeDistribution') or [], 'age', 'playSongNum', ' songs')}</div>
</div>
<div class="two" style="margin-top:16px">
<div class="panel"><h3>Annual footprint</h3><p class="sub">网易云目前返回的历年足迹；展示每年 playNum，不伪造缺失年份。</p>{_fact_rows(pf.get('yearItems') or [], 'year', 'playNum', ' plays')}</div>
<div class="panel"><h3>Listening rhythm</h3><p class="sub">当前月度六个时段的原生 duration 值，保持网易云原始口径。</p>{_fact_rows(pf.get('monthTimePeriods') or [], 'period', 'duration')}</div>
</div></section>
<section class="section" id="taste"><div class="section-head"><div><div class="pill">Taste map</div><h2>偏好不是一个标签</h2></div><p>先展示能稳定从歌曲元数据和行为数据推出的结构；曲风 API 可用时保留原始 provider payload，后续继续做风格层解析。</p></div><div class="three"><div class="panel"><h3>Albums in the record</h3>{_bars(metrics['topAlbums'],'playCount')}</div><div class="panel"><h3>Release decades</h3><p class="sub">按本次可恢复歌曲的发行时间计数。</p>{_decade_bars(metrics['releaseDecades'])}</div><div class="panel"><h3>Hidden favorites</h3><p class="sub">播放很多、但当前红心列表中没有出现的候选，不等于“你其实喜欢”。</p>{_bars(metrics['hiddenFavorites'],'playCount')}</div></div></section>
<section class="section" id="library"><div class="section-head"><div><div class="pill">Library</div><h2>你的歌单版图</h2></div><p>自建和收藏歌单分开统计；曲目能否恢复取决于歌单权限和接口覆盖。</p></div><div class="two"><div class="panel"><h3>Largest playlists</h3><p class="sub">按 trackCount 排序，收藏歌单标记 subscribed。</p>{_bars(metrics['topPlaylists'],'trackCount',' tracks')}</div><div class="panel"><h3>Library signals</h3>{metric_card('Liked share', f"{idx['likedShareObserved']}%" if idx['likedShareObserved'] is not None else None, '长期排行中，同时存在于当前红心 ID 的歌曲比例。')}{metric_card('Observed liked', s['likedObserved'], '长期排行与当前红心列表的交集数量。','Observed')}</div></div></section>
<section class="section" id="coverage"><div class="section-head"><div><div class="pill">Evidence layer</div><h2>Data coverage</h2></div><p>Coverage 反映这次同步真正拿到了哪些来源。接口失败、隐私设置或历史不可恢复，都不会被解释成“没有发生”。</p></div><div class="panel coverage"><div class="ring"><b>{cov['score']}%</b></div><div class="caps">{''.join(f'<div class="cap yes">✓ {esc(x)}</div>' for x in cov['available'])}{''.join(f'<div class="cap no">○ {esc(x)}</div>' for x in cov['missing'])}</div></div></section>
<footer>Observed facts → deterministic normalization → derived metrics → static report. Raw API responses and login credentials are not embedded in this Page. <span hidden>{esc(raw_json)}</span></footer>
</main></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_doc, encoding="utf-8")
