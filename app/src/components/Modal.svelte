<script>
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let player
  export let onClose

  let canvas
  let chart
  let chartMode = 'ppg'
  let weeklyData = null

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

  function getOpponentMult(opponent) {
    const pts = DEFENSE_RANKINGS[opponent] ?? LEAGUE_AVG
    return pts / LEAGUE_AVG
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


  onMount(async() => {
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
        const res = await fetch(`http://localhost:8000/api/schedule/${player.team}`)
        weeklyData = await res.json()
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
    {#if weeklyData && weeklyData.length > 0}
      <div class="weekly-scroll-section">
        <h3>2026 Schedule Projections <span class="placeholder-tag">placeholder</span></h3>
        <div class="weekly-scroll">
          {#each weeklyData as week}
            <div class="week-card">
              <span class="week-num">Wk {week.week}</span>
              <img 
                class="week-logo"
                src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`}
                alt={week.opponent}
                title={week.home ? week.opponent : `@${week.opponent}`}
              />
              <span class="week-away" style={week.home ? 'visibility: hidden' : ''}>@</span>
              <span class="week-pts pts">{(player.projected_points / 17 * getOpponentMult(week.opponent)).toFixed(1)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
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

  .weekly-scroll-section {
    margin-bottom: 1.5rem;
  }

.weekly-scroll-section h3 {
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

  .week-opp {
    font-size: 0.8rem;
    color: #f9fafb;
    font-weight: 600;
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

  .pos-badge.QB  { background: #2d0a1e; color: #fc2b6d; }
  .pos-badge.RB  { background: #0a2420; color: #20ceb8; }
  .pos-badge.WR  { background: #0f1f35; color: #59a7ff; }
  .pos-badge.TE  { background: #2d1a08; color: #feae58; }
  .pos-badge.K   { background: #1e0a2d; color: #c96cff; }
  .pos-badge.DEF { background: #2d1508; color: #bf5f40; }
</style>