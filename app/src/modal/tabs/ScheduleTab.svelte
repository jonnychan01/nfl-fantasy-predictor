<script>
  import { onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let data  

  let barCanvas
  let barChart

  $: weeks = data?.weeks ?? []
  $: bestMatchups = data?.best_matchups ?? []
  $: worstMatchups = data?.worst_matchups ?? []

  $: if (weeks.length > 0 && barCanvas) {
    if (barChart) barChart.destroy()

    const projections = weeks.map(w => w.projected)
    const max = Math.max(...projections)
    const min = Math.min(...projections)

    barChart = new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: weeks.map(w => `Wk ${w.week}`),
        datasets: [{
          label: 'Projected Points',
          data: projections,
          backgroundColor: projections.map(p => {
            if (p >= max * 0.9) return 'rgba(52, 211, 153, 0.8)'
            if (p <= min * 1.1) return 'rgba(248, 113, 113, 0.8)'
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

{#if weeks.length > 0}
  <div class="best-worst">
    {#each [{ label: 'Best Matchups', color: '#34d399', items: bestMatchups }, { label: 'Worst Matchups', color: '#f87171', items: worstMatchups }] as group}
      <div class="bw-group">
        <span class="bw-title" style="color: {group.color}">{group.label}</span>
        {#each group.items as week}
          <div class="bw-row">
            <img class="bw-logo" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
            <span class="bw-opp">{week.home ? '' : '@'}{week.opponent}</span>
            <span class="bw-week">Wk {week.week}</span>
            <span class="bw-pts" style="color: {group.color}">{week.projected.toFixed(1)}</span>
          </div>
        {/each}
      </div>
    {/each}
  </div>

  <div class="weekly-scroll-section">
    <h3>2026 Schedule Projections <span class="placeholder-tag">placeholder</span></h3>
    <div class="weekly-scroll">
      {#each weeks as week}
        <div class="week-card">
          <span class="week-num">Wk {week.week}</span>
          <img class="week-logo" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
          <span class="week-away" style={week.home ? 'visibility: hidden' : ''}>@</span>
          <span class="week-pts pts">{week.projected.toFixed(1)}</span>
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