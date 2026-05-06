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

  $: ppgDelta = (latest.ppg ?? 0) - (prev.ppg ?? 0)
  $: ptsDelta = (latest.pts_ppr ?? 0) - (prev.pts_ppr ?? 0)

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

  const SECTION_LABEL = 'text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2'
  const STAT_CARD = 'bg-surface border border-border-soft rounded-[10px] p-3.5 flex flex-col gap-1'
  const SEASON_STAT = 'flex-1 min-w-[70px] bg-surface border border-border-soft rounded-lg px-3 py-2.5'

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
  <div class="flex items-center justify-center h-[200px] text-gray-500 text-sm">Loading stats...</div>
{:else if weeks.length === 0}
  <div class="flex items-center justify-center h-[200px] text-gray-500 text-sm">No stats available</div>
{:else}

  <div class={SECTION_LABEL}>2026 Projection</div>
  <div class="grid grid-cols-3 gap-3">
    <div class="{STAT_CARD} border-t-2 !border-t-emerald-400">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Projected pts</span>
      <span class="text-[1.55rem] font-bold text-gray-50 leading-none">{player.projected_points}</span>
      <span class="text-xs text-gray-500">Full season PPR</span>
    </div>
    <div class="{STAT_CARD} border-t-2 !border-t-blue-500">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Proj PPG</span>
      <span class="text-[1.55rem] font-bold text-gray-50 leading-none">{(player.projected_points / 17).toFixed(1)}</span>
      <span class="text-xs text-gray-500">Per game avg</span>
    </div>
    <div class="{STAT_CARD} border-t-2 !border-t-yellow-400">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Consistency</span>
      <span class="text-[1.55rem] font-bold leading-none" style="color:{consistencyColor(consistencyPct)}">{consistencyPct}%</span>
      <span class="text-xs text-gray-500">{consistentWeeks} of {weeks.length} wks ≥85% avg</span>
    </div>
  </div>

  <div class="{SECTION_LABEL} mt-5">Boom / bust ({latestSeason})</div>
  <div class="flex gap-2 mb-3 justify-center max-w-[500px] mx-auto">
    <div class="{STAT_CARD} w-[290px] shrink-0">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Boom weeks</span>
      <span class="text-[1.15rem] font-bold leading-none text-emerald-400">{boomWeeks.length}</span>
      <span class="text-xs text-gray-500">≥130% of avg</span>
    </div>
    <div class="{STAT_CARD} w-[290px] shrink-0">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Avg game</span>
      <span class="text-[1.15rem] font-bold text-gray-50 leading-none">{avgPts.toFixed(1)}</span>
      <span class="text-xs text-gray-500">PPR pts</span>
    </div>
    <div class="{STAT_CARD} w-[290px] shrink-0">
      <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">Bust weeks</span>
      <span class="text-[1.15rem] font-bold leading-none text-red-400">{bustWeeks.length}</span>
      <span class="text-xs text-gray-500">≤55% of avg</span>
    </div>
  </div>
  <div class="flex items-center gap-3 mb-1.5 max-w-[500px] mx-auto">
    <div class="flex-1 h-[7px] bg-border-soft rounded-full overflow-hidden">
      <div class="h-full rounded-full" style="width:{consistencyPct}%;background:{consistencyColor(consistencyPct)}"></div>
    </div>
    <span class="text-sm font-bold text-gray-50 min-w-[36px] text-right">{consistencyPct}%</span>
  </div>
  <p class="text-[0.72rem] text-gray-500 text-center m-0">{consistencyLabel(consistencyPct)}</p>

  <div class="{SECTION_LABEL} mt-5">Season over season</div>
  <div class="flex gap-2 flex-wrap">
    <div class={SEASON_STAT}>
      <div class="text-base font-bold text-gray-50">{latest.ppg ?? '—'}</div>
      <div class="text-[0.6rem] font-semibold uppercase tracking-wider text-gray-500 mt-0.5">PPG</div>
      {#if prevSeason && prev.ppg}
        <div class="text-[0.68rem] font-semibold mt-0.5 {ppgDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}">
          {ppgDelta >= 0 ? '▲' : '▼'} {Math.abs(ppgDelta).toFixed(2)} vs {prevSeason}
        </div>
      {/if}
    </div>
    <div class={SEASON_STAT}>
      <div class="text-base font-bold text-gray-50">{latest.pts_ppr ?? '—'}</div>
      <div class="text-[0.6rem] font-semibold uppercase tracking-wider text-gray-500 mt-0.5">Total pts</div>
      {#if prevSeason && prev.pts_ppr}
        <div class="text-[0.68rem] font-semibold mt-0.5 {ptsDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}">
          {ptsDelta >= 0 ? '▲' : '▼'} {Math.abs(ptsDelta).toFixed(2)} vs {prevSeason}
        </div>
      {/if}
    </div>
    {#each extraCols as key}
    <div class={SEASON_STAT}>
      <div class="text-base font-bold text-gray-50">{latest[key] ?? '—'}</div>
      <div class="text-[0.6rem] font-semibold uppercase tracking-wider text-gray-500 mt-0.5">{SEASON_LABELS[key]}</div>
      {#if prev[key] != null && latest[key] != null}
        {@const delta = (latest[key] ?? 0) - (prev[key] ?? 0)}
        <div class="text-[0.68rem] font-semibold mt-0.5 {delta >= 0 ? 'text-emerald-400' : 'text-red-400'}">
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(0)} vs {prevSeason}
        </div>
      {/if}
    </div>
  {/each}
  </div>

{/if}
