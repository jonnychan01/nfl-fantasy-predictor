<script>
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let player
  export let onClose

  let canvas
  let chart
  let chartMode = 'ppg'
  let opponent = ''
  let weeklyProjection = null

  const NFL_TEAMS = ['ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAX','KC','LAC','LAR','LV','MIA','MIN','NE','NO','NYG','NYJ','PHI','PIT','SEA','SF','TB','TEN','WAS']

  async function fetchWeekly() {
    if (!opponent) {
      weeklyProjection = null
      return
    }
    const res = await fetch(`http://localhost:8000/api/players/${player.player_id}/weekly?opponent=${opponent}`)
    weeklyProjection = await res.json()
  }

  function toggleChart() {
  chartMode = chartMode === 'ppg' ? 'total' : 'ppg'
  updateChart()
  }

  function updateChart() {
  const seasons = player.seasons
  const historicalLabels = Object.keys(seasons).sort()

  const historicalData = historicalLabels.map(k => 
      chartMode === 'ppg' 
      ? (seasons[k].ppg ?? 0) 
      : (seasons[k].pts_ppr ?? 0)
  )

  const projectedValue = chartMode === 'ppg' 
      ? player.projected_points / 17 
      : player.projected_points

  chart.data.datasets[0].data = [...historicalData, null]
  chart.data.datasets[1].data = [...historicalData.map(() => null), projectedValue]
  chart.data.datasets[2].data = [
      ...historicalData.map((_, i) => i === historicalData.length - 1 ? historicalData[historicalData.length - 1] : null),
      projectedValue
  ]
  chart.update()
  }


  onMount(() => {
    const seasons = player.seasons
    const historicalLabels = Object.keys(seasons).sort()
    const historicalData = historicalLabels.map(k => seasons[k].ppg ?? 0)

    const labels = [...historicalLabels, '2026']
    const lastPpg = historicalData[historicalData.length - 1]
    const projectedPpg = player.projected_points / 17

    chart = new Chart(canvas, {
        type: 'line',
        data: {
        labels,
        datasets: [
            {
            label: 'PPG',
            data: [...historicalData, null],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            pointBackgroundColor: '#3b82f6',
            pointRadius: 5,
            tension: 0.3,
            fill: true,
            },
            {
            label: 'Projected 2026',
            data: [...historicalData.map(() => null), projectedPpg],
            borderColor: '#34d399',
            backgroundColor: 'rgba(52, 211, 153, 0.1)',
            borderWidth: 2,
            borderDash: [5, 5],
            pointBackgroundColor: '#34d399',
            pointRadius: 5,
            pointBorderColor: '#34d399',
            tension: 0.3,
            fill: false,
            },
            {
            label: 'Projection line',
            data: [...historicalData.map((_, i) => i === historicalData.length - 1 ? lastPpg : null), projectedPpg],
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
            legend: {
            display: true,
            labels: {
                color: '#9ca3af',
                filter: (item) => item.text !== 'Projection line'
            }
            },
        },
        scales: {
            x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
            y: { min: 0, ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
        }
        }
    })
    })

  onDestroy(() => chart?.destroy())
</script>

<div class="overlay" 
  on:click={onClose}
  on:keydown={(e) => e.key === 'Escape' && onClose()}
  role="button"
  tabindex="0"
>
  <div class="modal" 
    on:click|stopPropagation
    on:keydown|stopPropagation
    role="dialog"
    tabindex="-1"
  >
    <div class="modal-header">
      <div>
        <h2>{player.name}</h2>
        <span class="pos-badge {player.position}">{player.position}</span>
        <span class="team">{player.team}</span>
      </div>
      <button class="close" on:click={onClose}>✕</button>
    </div>
    <div class="stats">
      <div class="stat"><span>Age</span><strong>{player.age ?? '—'}</strong></div>
      <div class="stat"><span>Experience</span><strong>{player.years_experience}y</strong></div>
      <div class="stat"><span>Projected</span><strong class="pts">{player.projected_points}</strong></div>
    </div>
    <div class="weekly-section">
    <h3>Weekly Projection</h3>
    <div class="weekly-controls">
      <select bind:value={opponent} on:change={fetchWeekly}>
        <option value="">Select opponent...</option>
        {#each NFL_TEAMS as team}
          <option value={team}>{team}</option>
        {/each}
      </select>
        {#if weeklyProjection}
          <div class="weekly-result">
            <span>vs {opponent}</span>
            <strong class="pts">{weeklyProjection.adjusted_projection} pts</strong>
            <span class="mult">(opp mult: {weeklyProjection.opponent_multiplier}x)</span>
          </div>
        {/if}
      </div>
    </div>
    <div class="chart-toggle">
      <button 
        class:active={chartMode === 'ppg'} 
        on:click={() => { chartMode = 'ppg'; updateChart() }}
      >PPG</button>
      <button 
        class:active={chartMode === 'total'} 
        on:click={() => { chartMode = 'total'; updateChart() }}
      >Total Pts</button>
    </div>
    <canvas bind:this={canvas}></canvas>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .modal {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 2rem;
    width: 95%;
    max-width: 1000px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  h2 {
    margin: 0 0 0.4rem;
    color: #f9fafb;
  }

  .team {
    font-size: 0.85rem;
    color: #9ca3af;
    margin-left: 0.5rem;
  }

  .close {
    background: none;
    border: none;
    color: #9ca3af;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 0;
  }

  .stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
    font-size: 0.85rem;
    color: #9ca3af;
  }

  .stat strong {
    font-size: 1.1rem;
    color: #f9fafb;
    margin-top: 0.2rem;
  }

  .pts { color: #34d399 !important; }

  .pos-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  .chart-toggle {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  } 

  .chart-toggle button {
    padding: 0.3rem 0.8rem;
    border: 1px solid #374151;
    background: #1f2937;
    color: #9ca3af;
    border-radius: 999px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
  }

  .chart-toggle button.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
  }

  .pos-badge.QB  { background: #2d0a1e; color: #fc2b6d; }
  .pos-badge.RB  { background: #0a2420; color: #20ceb8; }
  .pos-badge.WR  { background: #0f1f35; color: #59a7ff; }
  .pos-badge.TE  { background: #2d1a08; color: #feae58; }
  .pos-badge.K   { background: #1e0a2d; color: #c96cff; }
  .pos-badge.DEF { background: #2d1508; color: #bf5f40; }
</style>