<script>
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let player

  let canvas
  let chart
  let chartMode = 'ppg'

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

<style>
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
</style>