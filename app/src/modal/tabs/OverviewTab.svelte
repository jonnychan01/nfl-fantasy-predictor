<script>
  import { onMount } from 'svelte'

  export let player
  export let weeklyData = null

  let weeks = []
  let loading = true

  $: seasons = Object.keys(player.seasons).sort()
  $: latestSeason = seasons[seasons.length - 1]
  $: prevSeason   = seasons[seasons.length - 2]
  $: latest = player.seasons[latestSeason] ?? {}
  $: prev   = player.seasons[prevSeason]   ?? {}

  $: avgPts = weeks.length
    ? weeks.reduce((a, w) => a + (w.stats?.pts_ppr ?? 0), 0) / weeks.length
    : 0

  $: consistentWeeks = weeks.filter(w => (w.stats?.pts_ppr ?? 0) >= avgPts * 0.85).length
  $: consistencyPct  = weeks.length ? Math.round((consistentWeeks / weeks.length) * 100) : 0
  $: boomWeeks = weeks.filter(w => (w.stats?.pts_ppr ?? 0) >= avgPts * 1.3)
  $: bustWeeks = weeks.filter(w => (w.stats?.pts_ppr ?? 0) <= avgPts * 0.55)

  $: topGame = [...weeks].sort((a, b) => (b.stats?.pts_ppr ?? 0) - (a.stats?.pts_ppr ?? 0))[0]
  $: botGame = [...weeks].sort((a, b) => (a.stats?.pts_ppr ?? 0) - (b.stats?.pts_ppr ?? 0))[0]
  $: maxPts  = weeks.length ? Math.max(...weeks.map(w => w.stats?.pts_ppr ?? 0)) : 1

  $: ppgDelta = (latest.ppg ?? 0) - (prev.ppg ?? 0)
  $: ptsDelta = (latest.pts_ppr ?? 0) - (prev.pts_ppr ?? 0)

  const BAR_H = 50

  function chipColor(pts) {
    if (pts >= avgPts * 1.3) return '#34d399'
    if (pts <= avgPts * 0.55) return '#f87171'
    return '#facc15'
  }

  function consistencyColor(pct) {
    if (pct >= 70) return '#34d399'
    if (pct >= 50) return '#facc15'
    return '#f87171'
  }

  function consistencyLabel(pct) {
    if (pct >= 70) return 'Highly reliable floor — safe weekly starter'
    if (pct >= 50) return 'Moderate consistency — matchup dependent'
    return 'Volatile — high ceiling, risky floor'
  }

  const SEASON_COLS = {
    QB:  ['pass_yards','pass_touchdowns','rush_touchdowns'],
    RB:  ['rush_yards','rush_touchdowns','rec'],
    WR:  ['rec','rec_yards','rec_touchdowns'],
    TE:  ['rec','rec_yards','rec_touchdowns'],
    K:   [],
    DEF: [],
  }
  const SEASON_LABELS = {
    pass_yards:'Pass Yds', pass_touchdowns:'Pass TDs', rush_touchdowns:'Rush TDs',
    rush_yards:'Rush Yds', rec:'Rec', rec_yards:'Rec Yds', rec_touchdowns:'Rec TDs',
  }

  $: extraCols = SEASON_COLS[player.position] ?? SEASON_COLS.WR

  onMount(async () => {
    try {
      const res = await fetch(
        `https://api.sleeper.com/stats/nfl/player/${player.player_id}?season=${latestSeason}&season_type=regular&grouping=week`
      )
      const raw = await res.json()
      weeks = Object.values(raw)
        .filter(w => w !== null && w.stats && w.stats.gp === 1)
        .sort((a, b) => a.week - b.week)
    } catch (e) {
      console.error('Failed to fetch weekly stats:', e)
      weeks = []
    } finally {
      loading = false
    }
  })
</script>

{#if loading}
  <div class="empty-state">Loading stats...</div>
{:else if weeks.length === 0}
  <div class="empty-state">No stats available</div>
{:else}

  <div class="section-label">2026 Projection</div>
  <div class="hero">
    <div class="stat-card accent-green">
      <span class="label">Projected pts</span>
      <span class="value">{player.projected_points}</span>
      <span class="sub">Full season PPR</span>
    </div>
    <div class="stat-card accent-blue">
      <span class="label">Proj PPG</span>
      <span class="value">{(player.projected_points / 17).toFixed(1)}</span>
      <span class="sub">Per game avg</span>
    </div>
    <div class="stat-card accent-yellow">
      <span class="label">Consistency</span>
      <span class="value" style="color:{consistencyColor(consistencyPct)}">{consistencyPct}%</span>
      <span class="sub">{consistentWeeks} of {weeks.length} wks ≥85% avg</span>
    </div>
  </div>

  <div class="section-label" style="margin-top:1.25rem">Boom / bust ({latestSeason})</div>
  <div class="bbd-row" style="justify-content:center">
    <div class="stat-card" style="width:290px;flex-shrink:0">
      <span class="label">Boom weeks</span>
      <span class="value sm green">{boomWeeks.length}</span>
      <span class="sub">≥130% of avg</span>
    </div>
    <div class="stat-card" style="width:290px;flex-shrink:0">
      <span class="label">Avg game</span>
      <span class="value sm">{avgPts.toFixed(1)}</span>
      <span class="sub">PPR pts</span>
    </div>
    <div class="stat-card" style="width:290px;flex-shrink:0">
      <span class="label">Bust weeks</span>
      <span class="value sm red">{bustWeeks.length}</span>
      <span class="sub">≤55% of avg</span>
    </div>
  </div>
  <div class="consistency-row" style="max-width:500px;margin:0 auto 0.35rem">
    <div class="bar-track">
      <div class="bar-fill" style="width:{consistencyPct}%;background:{consistencyColor(consistencyPct)}"></div>
    </div>
    <span class="consistency-val">{consistencyPct}%</span>
  </div>
  <p class="consistency-sub" style="text-align:center">{consistencyLabel(consistencyPct)}</p>

  <div class="section-label" style="margin-top:1.25rem">Season over season</div>
  <div class="season-row">
    <div class="season-stat">
      <div class="sv">{latest.ppg ?? '—'}</div>
      <div class="sl">PPG</div>
      {#if prevSeason && prev.ppg}
        <div class="delta" class:up={ppgDelta >= 0} class:down={ppgDelta < 0}>
          {ppgDelta >= 0 ? '▲' : '▼'} {Math.abs(ppgDelta).toFixed(2)} vs {prevSeason}
        </div>
      {/if}
    </div>
    <div class="season-stat">
      <div class="sv">{latest.pts_ppr ?? '—'}</div>
      <div class="sl">Total pts</div>
      {#if prevSeason && prev.pts_ppr}
        <div class="delta" class:up={ptsDelta >= 0} class:down={ptsDelta < 0}>
          {ptsDelta >= 0 ? '▲' : '▼'} {Math.abs(ptsDelta).toFixed(2)} vs {prevSeason}
        </div>
      {/if}
    </div>
    {#each extraCols as key}
    <div class="season-stat">
      <div class="sv">{latest[key] ?? '—'}</div>
      <div class="sl">{SEASON_LABELS[key]}</div>
      {#if prev[key] != null && latest[key] != null}
        {@const delta = (latest[key] ?? 0) - (prev[key] ?? 0)}
        <div class="delta" class:up={delta >= 0} class:down={delta < 0}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(0)} vs {prevSeason}
        </div>
      {/if}
    </div>
  {/each}
  </div>

{/if}

<style>
  .empty-state {
    display: flex; 
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #6b7280; 
    font-size: 0.9rem;
  }

  .section-label {
    color: #9ca3af; 
    font-size: 0.75rem; 
    font-weight: 600;
    text-transform: uppercase; 
    letter-spacing: 0.07em; 
    margin-bottom: 0.5rem;
  }

  .hero { 
    display: grid; 
    grid-template-columns: 1fr 1fr 1fr; 
    gap: 0.75rem; 
  }

  .bbd-row { 
    display: flex; 
    gap: 0.5rem; 
    margin-bottom: 0.75rem; 
    justify-content: center; 
    max-width: 500px; 
    margin-left: auto; 
    margin-right: auto; 
  }

  .stat-card {
    background: #111827; 
    border: 1px solid #1f2937;
    border-radius: 10px; 
    padding: 0.85rem;
    display: flex; 
    flex-direction: column; 
    gap: 0.2rem;
  }

  .stat-card.accent-blue   { 
    border-top: 2px 
    solid #3b82f6; 
  }

  .stat-card.accent-green  { 
    border-top: 2px 
    solid #34d399; 
  }

  .stat-card.accent-yellow { 
    border-top: 2px 
    solid #facc15; 
  }

  .label { 
    font-size: 0.62rem; 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 0.07em; 
    color: #6b7280;
   }

  .value { 
    font-size: 1.55rem; 
    font-weight: 700; 
    color: #f9fafb; 
    line-height: 1; 
  }

  .value.sm { 
    font-size: 1.15rem; 
  }

  .value.green { 
    color: #34d399; 
  }

  .value.red   {
     color: #f87171; 
  }
  
  .sub {
     font-size: 0.7rem; 
     color: #6b7280; 
    }

  .consistency-row {
     display: flex; 
     align-items: center; 
     gap: 0.75rem; 
     margin-bottom: 0.35rem; 
    }

  .bar-track { 
    flex: 1; 
    height: 7px; 
    background: #1f2937; 
    border-radius: 999px; 
    overflow: hidden; 
  }

  .bar-fill  { 
    height: 100%; 
    border-radius: 999px; 
  }

  .consistency-val {
    font-size: 0.85rem; 
    font-weight: 700; 
    color: #f9fafb; 
    min-width: 36px; 
    text-align: right; 
  }

  .consistency-sub { 
    font-size: 0.72rem; 
    color: #6b7280; 
    margin-bottom: 0; 
  }

  .season-row { 
    display: flex; 
    gap: 0.5rem; 
    flex-wrap: wrap;
   }

  .season-stat {
    flex: 1; 
    min-width: 70px;
    background: #111827; 
    border: 1px solid #1f2937;
    border-radius: 8px; 
    padding: 0.6rem 0.75rem;
  }
  .sv { 
    font-size: 1.05rem; 
    font-weight: 700; 
    color: #f9fafb; 
  }

  .sl { 
    font-size: 0.6rem; 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 0.06em; 
    color: #6b7280; 
    margin-top: 0.15rem; 
  }

  .delta { 
    font-size: 0.68rem; 
    font-weight: 600; 
    margin-top: 0.2rem; 
  }

  .delta.up   { 
    color: #34d399; 
  }

  .delta.down { 
    color: #f87171; 
    }
</style>