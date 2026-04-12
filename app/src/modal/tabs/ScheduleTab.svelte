<script>
  import { onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let player
  export let weeklyData

  let barCanvas
  let barChart

  const DEFENSE_RANKINGS = {
    "SF": 17.2, "BAL": 18.1, "BUF": 18.4, "PHI": 18.9, "KC": 19.2,
    "MIN": 19.8, "DET": 20.1, "GB": 20.4, "PIT": 20.7, "LAC": 21.0,
    "HOU": 21.3, "WAS": 21.6, "CLE": 21.9, "SEA": 22.1, "DAL": 22.4,
    "MIA": 22.7, "TB": 23.0, "ATL": 23.2, "LAR": 23.5, "DEN": 23.8,
    "IND": 24.0, "CIN": 24.3, "NYJ": 24.6, "LV": 24.9, "JAX": 25.2,
    "NE": 25.5, "NYG": 25.8, "ARI": 26.1, "CHI": 26.4, "NO": 26.7,
    "CAR": 27.0, "TEN": 27.3
  }

  const LEAGUE_AVG = Object.values(DEFENSE_RANKINGS).reduce((a, b) => a + b, 0) / Object.keys(DEFENSE_RANKINGS).length

  $: weeklyMultipliers = (() => {
    if (!weeklyData) return []
    const rawMults = weeklyData.map(w => DEFENSE_RANKINGS[w.opponent] ?? LEAGUE_AVG)
    const scheduleAvg = rawMults.reduce((a, b) => a + b, 0) / rawMults.length
    return rawMults.map(m => m / scheduleAvg)
  })()

  $: bestWorst = (() => {
    if (!weeklyData || weeklyData.length === 0) return null
    const weeks = weeklyData.map((w, i) => ({
      ...w,
      projected: player.projected_points / 17 * weeklyMultipliers[i]
    })).sort((a, b) => b.projected - a.projected)
    return {
      best: weeks.slice(0, 3),
      worst: weeks.slice(-3).reverse()
    }
  })()

  $: if (weeklyData && weeklyMultipliers.length > 0 && barCanvas) {
    if (barChart) barChart.destroy()
    barChart = new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: weeklyData.map(w => `Wk ${w.week}`),
        datasets: [{
          label: 'Projected Points',
          data: weeklyMultipliers.map(m => player.projected_points / 17 * m),
          backgroundColor: weeklyMultipliers.map(m => {
            const pts = player.projected_points / 17 * m
            const all = weeklyMultipliers.map(m2 => player.projected_points / 17 * m2)
            if (pts >= Math.max(...all) * 0.9) return 'rgba(52, 211, 153, 0.8)'
            if (pts <= Math.min(...all) * 1.1) return 'rgba(248, 113, 113, 0.8)'
            return 'rgba(250, 204, 21, 0.8)'
          }),
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
          y: { min: 0, ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
        }
      }
    })
  }

  onDestroy(() => barChart?.destroy())
</script>

{#if weeklyData && weeklyData.length > 0}

  {#if bestWorst}
    <div class="best-worst">
      <div class="bw-group">
        <span class="bw-title" style="color: #34d399">Best Matchups</span>
        {#each bestWorst.best as week}
          <div class="bw-row">
            <img class="bw-logo" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
            <span class="bw-opp">{week.home ? '' : '@'}{week.opponent}</span>
            <span class="bw-week">Wk {week.week}</span>
            <span class="bw-pts" style="color: #34d399">{week.projected.toFixed(1)}</span>
          </div>
        {/each}
      </div>
      <div class="bw-group">
        <span class="bw-title" style="color: #f87171">Worst Matchups</span>
        {#each bestWorst.worst as week}
          <div class="bw-row">
            <img class="bw-logo" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
            <span class="bw-opp">{week.home ? '' : '@'}{week.opponent}</span>
            <span class="bw-week">Wk {week.week}</span>
            <span class="bw-pts" style="color: #f87171">{week.projected.toFixed(1)}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <div class="weekly-scroll-section">
    <h3>2026 Schedule Projections <span class="placeholder-tag">placeholder</span></h3>
    <div class="weekly-scroll">
      {#each weeklyData as week, i}
        <div class="week-card">
          <span class="week-num">Wk {week.week}</span>
          <img 
            class="week-logo"
            src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`}
            alt={week.opponent}
            title={week.home ? week.opponent : `@${week.opponent}`}
          />
          <span class="week-away" style={week.home ? 'visibility: hidden' : ''}>@</span>
          <span class="week-pts pts">{(player.projected_points / 17 * weeklyMultipliers[i]).toFixed(1)}</span>
        </div>
      {/each}
    </div>
  </div>

  <div class="bar-chart-section">
    <h3>Weekly Breakdown</h3>
    <canvas bind:this={barCanvas} style="max-height: 180px;"></canvas>
  </div>
{:else}
  <div class="empty-tab"><p>Loading schedule...</p></div>
{/if}

<style>
  .weekly-scroll-section {
    margin-bottom: 1.5rem;
  }

  h3 {
    color: #9ca3af;
    font-size: 0.85rem;
    margin-bottom: 0.75rem;
  }

  .placeholder-tag {
    font-size: 0.7rem;
    background: #374151;
    color: #6b7280;
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 0.5rem;
  }

  .weekly-scroll {
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .week-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    min-width: 70px;
    flex-shrink: 0;
  }

  .week-num {
    font-size: 0.7rem;
    color: #6b7280;
  }

  .week-pts {
    font-size: 0.85rem;
  }

  .week-logo {
    width: 40px;
    height: 40px;
    object-fit: contain;
  }

  .week-away {
    font-size: 0.65rem;
    color: #6b7280;
    margin-top: -0.4rem;
  }

  .pts { color: #34d399 !important; }

  .best-worst {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
  }

  .bw-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .bw-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
  }

  .bw-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 0.4rem 0.75rem;
  }

  .bw-logo {
    width: 24px;
    height: 24px;
    object-fit: contain;
  }

  .bw-opp {
    font-size: 0.85rem;
    color: #f9fafb;
    font-weight: 600;
    flex: 1;
  }

  .bw-week {
    font-size: 0.75rem;
    color: #6b7280;
  }

  .bw-pts {
    font-size: 0.85rem;
    font-weight: 700;
  }

  .bar-chart-section {
    margin-top: 1.5rem;
    max-height: 180px;
    padding-bottom: 1.5rem;
  }

  .bar-chart-section h3 {
    color: #9ca3af;
    font-size: 0.85rem;
    margin-bottom: 0.75rem;
  }

  .empty-tab {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #6b7280;
    font-size: 0.9rem;
  }
</style>