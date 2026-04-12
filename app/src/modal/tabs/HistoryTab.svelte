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

  function getRowColor(pts, allWeeks) {
    if (!pts || allWeeks.length === 0) return ''
    const avg = allWeeks.reduce((a, w) => a + (w.stats?.pts_ppr ?? 0), 0) / allWeeks.length
    if (pts >= avg * 1.2) return 'row-good'
    if (pts <= avg * 0.8) return 'row-bad'
    return 'row-mid'
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

<div class="season-tabs">
  {#each seasons as season}
    <button
      class:active={selectedSeason === season}
      on:click={() => selectedSeason = season}
    >{season}</button>
  {/each}
</div>

<div class="table-wrapper">
  {#if loadingWeekly}
    <div class="empty-state">Loading...</div>
  {:else if weeklyData[selectedSeason]?.length}
    <table>
      <thead>
        <tr>
          <th>WK</th>
          <th>OPP</th>
          {#each columns as col}
            <th>{col.label}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each weeklyData[selectedSeason] as week}
          <tr class={getRowColor(week.stats?.pts_ppr, weeklyData[selectedSeason])}>
            <td>{week.week}</td>
            <td class="opp">{week.opponent ?? '—'}</td>
            {#each columns as col}
              <td class={col.key === 'pts_ppr' ? 'pts-cell' : ''}>{week.stats?.[col.key] ?? '—'}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <div class="empty-state">No data available</div>
  {/if}
</div>

<div class="trend-header">
  <h3 class="section-label">Career Trend</h3>
  <div class="legend">
    <span class="legend-item">
      <span class="dot blue"></span>Historical
    </span>
    <span class="legend-item">
      <span class="dot green"></span>Projected 2026
    </span>
  </div>
</div>

<div class="charts-row">
  <div class="chart-box">
    <p class="chart-title">PPG</p>
    <canvas bind:this={canvasPpg}></canvas>
  </div>
  <div class="chart-box">
    <p class="chart-title">Total Pts</p>
    <canvas bind:this={canvasTotal}></canvas>
  </div>
</div>

<style>
  .season-tabs {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .season-tabs button {
    padding: 0.3rem 0.8rem;
    border: 1px solid #374151;
    background: #1f2937;
    color: #9ca3af;
    border-radius: 999px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
  }

  .season-tabs button.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
  }

  .table-wrapper {
    overflow-x: auto;
    margin-bottom: 2rem;
    border-radius: 8px;
    border: 1px solid #1f2937;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.75rem;
  }

  thead tr { background: #111827; }

  th {
    padding: 0.35rem 0.5rem;
    text-align: right;
    color: #6b7280;
    font-weight: 600;
    font-size: 0.65rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  th:first-child, th:nth-child(2) { text-align: left; }

  td {
    padding: 0.3rem 0.5rem;
    text-align: right;
    color: #d1d5db;
    border-top: 1px solid #1f2937;
    white-space: nowrap;
  }

  td:first-child, td:nth-child(2) { text-align: left; }

  td.opp {
    color: #6b7280;
    font-size: 0.75rem;
  }

  td.pts-cell {
    font-weight: 700;
    color: #f9fafb;
  }

  tbody tr:hover { background: #1f2937; }

  tbody tr.row-good {
    border-left: 3px solid #34d399;
    background: rgba(52, 211, 153, 0.05);
  }

  tbody tr.row-bad {
    border-left: 3px solid #f87171;
    background: rgba(248, 113, 113, 0.05);
  }

  tbody tr.row-mid {
    border-left: 3px solid #facc15;
    background: rgba(250, 204, 21, 0.03);
  }

  tbody tr.row-good:hover { background: rgba(52, 211, 153, 0.1); }
  tbody tr.row-bad:hover  { background: rgba(248, 113, 113, 0.1); }
  tbody tr.row-mid:hover  { background: rgba(250, 204, 21, 0.07); }

  .empty-state {
    padding: 2rem;
    text-align: center;
    color: #6b7280;
    font-size: 0.85rem;
  }

  .trend-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }

  .section-label {
    color: #9ca3af;
    font-size: 0.85rem;
    font-weight: 600;
    margin: 0;
  }

  .legend {
    display: flex;
    gap: 0.75rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: #6b7280;
    font-size: 0.75rem;
  }

  .dot {
    width: 20px;
    height: 2px;
    border-radius: 1px;
  }

  .dot.blue { background: #3b82f6; }

  .dot.green {
    background: repeating-linear-gradient(
      to right,
      #34d399 0px, #34d399 4px,
      transparent 4px, transparent 8px
    );
  }

  .charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .chart-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 0.75rem;
  }

  .chart-title {
    color: #6b7280;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.5rem 0;
  }
</style>