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
  <div class="flex gap-8 mb-6">
    {#each [{ label: 'Best Matchups', color: '#34d399', items: bestMatchups }, { label: 'Worst Matchups', color: '#f87171', items: worstMatchups }] as group}
      <div class="flex flex-col gap-2 flex-1">
        <span class="text-xs font-bold uppercase tracking-wider mb-1" style="color: {group.color}">{group.label}</span>
        {#each group.items as week}
          <div class="flex items-center gap-2 bg-border-soft border border-border rounded-lg px-3 py-1.5">
            <img class="w-6 h-6 object-contain" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
            <span class="text-sm text-gray-50 font-semibold flex-1">{week.home ? '' : '@'}{week.opponent}</span>
            <span class="text-xs text-gray-500">Wk {week.week}</span>
            <span class="text-sm font-bold" style="color: {group.color}">{week.projected.toFixed(1)}</span>
          </div>
        {/each}
      </div>
    {/each}
  </div>

  <div class="mb-6">
    <h3 class="text-gray-400 text-sm mb-3">
      2026 Schedule Projections
      <span class="text-xs bg-border text-gray-500 px-1.5 py-px rounded ml-2">placeholder</span>
    </h3>
    <div class="flex gap-2 overflow-x-auto pb-2">
      {#each weeks as week}
        <div class="flex flex-col items-center gap-1 bg-border-soft border border-border rounded-lg px-3 py-2.5 min-w-[70px] shrink-0">
          <span class="text-xs text-gray-500">Wk {week.week}</span>
          <img class="w-10 h-10 object-contain" src={`https://sleepercdn.com/images/team_logos/nfl/${week.opponent?.toLowerCase()}.png`} alt={week.opponent} />
          <span class="text-[0.65rem] text-gray-500 -mt-1.5" style={week.home ? 'visibility: hidden' : ''}>@</span>
          <span class="text-sm text-emerald-400">{week.projected.toFixed(1)}</span>
        </div>
      {/each}
    </div>
  </div>

  <div class="mt-6 max-h-[180px] pb-6">
    <h3 class="text-gray-400 text-sm mb-3">Weekly Breakdown</h3>
    <canvas bind:this={barCanvas} style="max-height: 180px;"></canvas>
  </div>
{:else}
  <div class="flex items-center justify-center h-[200px] text-gray-500 text-sm"><p>Loading schedule...</p></div>
{/if}
