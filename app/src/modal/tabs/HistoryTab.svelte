<script>
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let player

  let canvasPpg
  let canvasTotal
  let chartPpg
  let chartTotal
  let selectedSeason = null
  let weeklyData = {}
  let loadingWeekly = false

  const POSITION_COLUMNS = {
    QB: [
      { key: 'pass_att',  label: 'ATT' },
      { key: 'pass_cmp',  label: 'CMP' },
      { key: 'pass_yd',   label: 'PASS YDS' },
      { key: 'pass_td',   label: 'PASS TD' },
      { key: 'pass_int',  label: 'INT' },
      { key: 'rush_yd',   label: 'RUSH YDS' },
      { key: 'rush_td',   label: 'RUSH TD' },
      { key: 'pts_ppr',   label: 'PTS' },
    ],
    RB: [
      { key: 'rush_att',  label: 'CAR' },
      { key: 'rush_yd',   label: 'RUSH YDS' },
      { key: 'rush_td',   label: 'RUSH TD' },
      { key: 'rec',       label: 'REC' },
      { key: 'rec_tgt',   label: 'TGT' },
      { key: 'rec_yd',    label: 'REC YDS' },
      { key: 'rec_td',    label: 'REC TD' },
      { key: 'pts_ppr',   label: 'PTS' },
    ],
    WR: [
      { key: 'rec_tgt',   label: 'TGT' },
      { key: 'rec',       label: 'REC' },
      { key: 'rec_yd',    label: 'REC YDS' },
      { key: 'rec_td',    label: 'REC TD' },
      { key: 'rush_yd',   label: 'RUSH YDS' },
      { key: 'pts_ppr',   label: 'PTS' },
    ],
    TE: [
      { key: 'rec_tgt',   label: 'TGT' },
      { key: 'rec',       label: 'REC' },
      { key: 'rec_yd',    label: 'REC YDS' },
      { key: 'rec_td',    label: 'REC TD' },
      { key: 'pts_ppr',   label: 'PTS' },
    ],
    K: [
      { key: 'fgm',       label: 'FGM' },
      { key: 'fga',       label: 'FGA' },
      { key: 'fgm_lng',   label: 'LNG' },
      { key: 'xpm',       label: 'XPM' },
      { key: 'pts_ppr',   label: 'PTS' },
    ],
    DEF: [
      { key: 'pts_ppr',   label: 'PTS' },
    ],
  }

  $: seasons = Object.keys(player.seasons).sort().reverse()
  $: columns = POSITION_COLUMNS[player.position] ?? POSITION_COLUMNS.WR

  $: if (seasons.length && selectedSeason === null) {
    selectedSeason = seasons[0]
  }

  async function fetchWeeklyData(season) {
    if (weeklyData[season]) return
    loadingWeekly = true
    try {
      const res = await fetch(
        `https://api.sleeper.com/stats/nfl/player/${player.player_id}?season=${season}&season_type=regular&grouping=week`
      )
      const raw = await res.json()
      weeklyData[season] = Object.values(raw)
        .filter(w => w !== null && w.stats && w.stats.gp === 1)
        .sort((a, b) => a.week - b.week)
    } catch (e) {
      weeklyData[season] = []
    } finally {
      loadingWeekly = false
    }
    weeklyData = { ...weeklyData }
  }

  $: if (selectedSeason) fetchWeeklyData(selectedSeason)

  function makeChartConfig(historicalLabels, historicalData, projectedValue, label) {
    const lastVal = historicalData[historicalData.length - 1]
    return {
      type: 'line',
      data: {
        labels: [...historicalLabels, '2026'],
        datasets: [
          {
            label,
            data: [...historicalData, null],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            pointBackgroundColor: '#3b82f6',
            pointRadius: 4,
            tension: 0.3,
            fill: true,
          },
          {
            label: 'Projected 2026',
            data: [...historicalData.map(() => null), projectedValue],
            borderColor: '#34d399',
            backgroundColor: 'rgba(52, 211, 153, 0.1)',
            borderWidth: 2,
            borderDash: [5, 5],
            pointBackgroundColor: '#34d399',
            pointRadius: 4,
            tension: 0.3,
            fill: false,
          },
          {
            label: 'Projection line',
            data: [...historicalData.map((_, i) => i === historicalData.length - 1 ? lastVal : null), projectedValue],
            borderColor: '#34d399',
            borderWidth: 1,
            borderDash: [5, 5],
            pointRadius: 0,
            tension: 0,
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 } }, grid: { color: '#1f2937' } },
          y: { min: 0, ticks: { color: '#9ca3af', font: { size: 10 } }, grid: { color: '#1f2937' } },
        }
      }
    }
  }

  function getRowClass(pts, allWeeks) {
    if (!pts || allWeeks.length === 0) return ''
    const avg = allWeeks.reduce((a, w) => a + (w.stats?.pts_ppr ?? 0), 0) / allWeeks.length
    if (pts >= avg * 1.2) return 'border-l-[3px] border-l-emerald-400 bg-emerald-400/5 hover:!bg-emerald-400/10'
    if (pts <= avg * 0.8) return 'border-l-[3px] border-l-red-400 bg-red-400/5 hover:!bg-red-400/10'
    return 'border-l-[3px] border-l-yellow-400 bg-yellow-400/[0.03] hover:!bg-yellow-400/[0.07]'
  }

  onMount(() => {
    const historicalLabels = Object.keys(player.seasons).sort()
    const ppgData = historicalLabels.map(k => player.seasons[k].ppg ?? 0)
    const totalData = historicalLabels.map(k => player.seasons[k].pts_ppr ?? 0)

    chartPpg   = new Chart(canvasPpg,   makeChartConfig(historicalLabels, ppgData,   player.projected_points / 17, 'PPG'))
    chartTotal = new Chart(canvasTotal, makeChartConfig(historicalLabels, totalData,  player.projected_points,      'Total Pts'))
  })

  onDestroy(() => {
    chartPpg?.destroy()
    chartTotal?.destroy()
  })
</script>

<div class="flex flex-wrap gap-1.5 mb-4">
  {#each seasons as season}
    <button
      class="px-3 py-1 rounded-full border text-[0.8rem] cursor-pointer transition-colors
        {selectedSeason === season
          ? 'bg-blue-500 border-blue-500 text-white'
          : 'bg-border-soft border-border text-gray-400'}"
      on:click={() => selectedSeason = season}
    >{season}</button>
  {/each}
</div>

<div class="overflow-x-auto mb-8 rounded-lg border border-border-soft">
  {#if loadingWeekly}
    <div class="p-8 text-center text-gray-500 text-sm">Loading...</div>
  {:else if weeklyData[selectedSeason]?.length}
    <table class="w-full border-collapse text-xs">
      <thead>
        <tr class="bg-surface">
          <th class="px-2 py-1.5 text-left text-gray-500 font-semibold text-[0.65rem] uppercase tracking-wider whitespace-nowrap">WK</th>
          <th class="px-2 py-1.5 text-left text-gray-500 font-semibold text-[0.65rem] uppercase tracking-wider whitespace-nowrap">OPP</th>
          {#each columns as col}
            <th class="px-2 py-1.5 text-right text-gray-500 font-semibold text-[0.65rem] uppercase tracking-wider whitespace-nowrap">{col.label}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each weeklyData[selectedSeason] as week}
          <tr class="hover:bg-border-soft {getRowClass(week.stats?.pts_ppr, weeklyData[selectedSeason])}">
            <td class="px-2 py-1 text-left text-gray-300 border-t border-border-soft whitespace-nowrap">{week.week}</td>
            <td class="px-2 py-1 text-left text-gray-500 text-xs border-t border-border-soft whitespace-nowrap">{week.opponent ?? '—'}</td>
            {#each columns as col}
              <td class="px-2 py-1 text-right border-t border-border-soft whitespace-nowrap {col.key === 'pts_ppr' ? 'font-bold text-gray-50' : 'text-gray-300'}">{week.stats?.[col.key] ?? '—'}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <div class="p-8 text-center text-gray-500 text-sm">No data available</div>
  {/if}
</div>

<div class="flex items-center gap-4 mb-3">
  <h3 class="text-gray-400 text-sm font-semibold m-0">Career Trend</h3>
  <div class="flex gap-3">
    <span class="flex items-center gap-1.5 text-gray-500 text-xs">
      <span class="w-5 h-0.5 rounded-sm bg-blue-500"></span>Historical
    </span>
    <span class="flex items-center gap-1.5 text-gray-500 text-xs">
      <span class="w-5 h-0.5 rounded-sm" style="background: repeating-linear-gradient(to right, #34d399 0px, #34d399 4px, transparent 4px, transparent 8px)"></span>Projected 2026
    </span>
  </div>
</div>

<div class="grid grid-cols-2 gap-4">
  <div class="bg-surface border border-border-soft rounded-lg p-3">
    <p class="text-gray-500 text-[0.72rem] font-semibold uppercase tracking-wider m-0 mb-2">PPG</p>
    <canvas bind:this={canvasPpg}></canvas>
  </div>
  <div class="bg-surface border border-border-soft rounded-lg p-3">
    <p class="text-gray-500 text-[0.72rem] font-semibold uppercase tracking-wider m-0 mb-2">Total Pts</p>
    <canvas bind:this={canvasTotal}></canvas>
  </div>
</div>
