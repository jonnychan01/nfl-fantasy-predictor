<script>
  import { onDestroy } from 'svelte'
  import Chart from 'chart.js/auto'

  export let player

  $: seasons = Object.keys(player?.seasons ?? {}).sort()
  $: latest = player?.seasons?.[seasons[seasons.length - 1]] ?? {}

  $: adp  = player?.adp ?? null
  $: diff = player?.adp_diff ?? null

  $: tagInfo = getTagInfo(player?.tag, diff)

  $: targetShare = latest.target_share ?? 0
  $: snapPct     = latest.snap_percentage ?? 0
  $: rzShare     = latest.rz_target_share ?? 0

  $: insights = buildInsights({
    position: player?.position,
    tag: player?.tag,
    diff,
    targetShare,
    snapPct,
    rzShare,
  })

  let canvasAdp
  let adpChart = null
  let adpHistory = null

  let depthData = null
  let depthLoading = false

  const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

  const SECTION_LABEL = 'text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2'
  const EMPTY = 'text-gray-600 text-[0.8rem] py-3 px-1'

  $: if (player?.player_id) {
    fetchAdpHistory(player.player_id)
    fetchDepthChart(player.player_id)
  }

  async function fetchAdpHistory(pid) {
    try {
      const res = await fetch(`http://localhost:8000/api/players/${pid}/adp-history`)
      adpHistory = await res.json()
    } catch (e) {
      console.error('ADP history fetch failed:', e)
      adpHistory = null
    }
  }

  async function fetchDepthChart(pid) {
    depthLoading = true
    try {
      const res = await fetch(`http://localhost:8000/api/players/${pid}/depth-chart`)
      depthData = await res.json()
    } catch (e) {
      console.error('Depth chart fetch failed:', e)
      depthData = null
    } finally {
      depthLoading = false
    }
  }

  $: if (canvasAdp && adpHistory) {
    buildAdpChart()
  }

  function buildAdpChart() {
    if (adpChart) { adpChart.destroy(); adpChart = null }
    if (!canvasAdp || !adpHistory) return

    const historical = adpHistory.historical ?? []
    const currentAdp = adpHistory.current_adp
    const estimatedAdp = adpHistory.estimated_adp

    const bluePoints = [...historical]
    if (currentAdp) bluePoints.push({ year: 2025, adp: currentAdp })

    const lastBlue = bluePoints[bluePoints.length - 1]
    const greenPoints = lastBlue && estimatedAdp
      ? [{ year: lastBlue.year, adp: lastBlue.adp }, { year: 2026, adp: estimatedAdp }]
      : []

    const allAdps = [...bluePoints.map(p => p.adp), ...greenPoints.map(p => p.adp)].filter(Boolean)
    const minAdp = Math.max(1, Math.min(...allAdps) - 15)
    const maxAdp = Math.min(220, Math.max(...allAdps) + 15)

    adpChart = new Chart(canvasAdp, {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'ADP',
            data: bluePoints.map(p => ({ x: p.year, y: p.adp })),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.08)',
            pointBackgroundColor: '#3b82f6',
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2,
            tension: 0.3,
            fill: false,
          },
          {
            label: 'Projected 2026',
            data: greenPoints.map(p => ({ x: p.year, y: p.adp })),
            borderColor: '#34d399',
            backgroundColor: 'transparent',
            pointBackgroundColor: '#34d399',
            pointRadius: (ctx) => ctx.dataIndex === 1 ? 5 : 0,
            pointHoverRadius: 6,
            borderWidth: 2,
            borderDash: [5, 4],
            tension: 0.1,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        scales: {
          x: {
            type: 'linear',
            min: bluePoints[0]?.year ?? 2021,
            max: greenPoints.length ? 2026 : 2025,
            ticks: {
              stepSize: 1,
              color: '#6b7280',
              font: { size: 10 },
              callback: v => String(v),
            },
            grid: { color: '#1f2937' },
          },
          y: {
            reverse: true,
            min: minAdp,
            max: maxAdp,
            ticks: {
              color: '#6b7280',
              font: { size: 10 },
              maxTicksLimit: 5,
            },
            grid: { color: '#1f2937' },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#111827',
            borderColor: '#374151',
            borderWidth: 1,
            titleColor: '#9ca3af',
            bodyColor: '#f9fafb',
            callbacks: {
              title: items => `${items[0].parsed.x}`,
              label: item => ` ADP: ${item.parsed.y}`,
            },
          },
        },
      },
    })
  }

  onDestroy(() => { if (adpChart) adpChart.destroy() })

  function getTagInfo(tag, d) {
    if (tag === 'sleeper') return { label: 'SLEEPER', color: '#34d399', bg: 'rgba(52,211,153,0.08)', border: '#10b981', icon: '💎', sub: d != null ? `+${d} spots of value` : '' }
    if (tag === 'bust')    return { label: 'BUST',    color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: '#dc2626', icon: '⚠️', sub: d != null ? `${d} spots of value` : '' }
    return { label: 'FAIR VALUE', color: '#9ca3af', bg: 'rgba(156,163,175,0.08)', border: '#6b7280', icon: '⚖️', sub: d != null ? `${d > 0 ? '+' : ''}${d} spots` : '' }
  }

  function buildInsights({ position, tag, diff, targetShare, snapPct, rzShare }) {
    const out = []
    const skill = ['WR','TE','RB'].includes(position)

    if (skill && targetShare >= 0.25)
      out.push({ icon: '🎯', text: `Elite target share of ${Math.round(targetShare*100)}% — likely the clear WR1 on his team.` })
    else if (skill && targetShare >= 0.18)
      out.push({ icon: '🎯', text: `Strong target share of ${Math.round(targetShare*100)}% — featured in the passing game.` })
    else if (skill && targetShare > 0 && targetShare < 0.10)
      out.push({ icon: '🎯', text: `Low target share of ${Math.round(targetShare*100)}% — secondary option in the offense.` })

    if (position !== 'K' && position !== 'DEF' && snapPct >= 0.85)
      out.push({ icon: '⚡', text: `${Math.round(snapPct*100)}% snap rate — an every-down player with maximum opportunity.` })
    else if (position !== 'K' && position !== 'DEF' && snapPct > 0 && snapPct <= 0.40)
      out.push({ icon: '⚡', text: `${Math.round(snapPct*100)}% snap rate — limited role on offense.` })

    if (skill && rzShare >= 0.20)
      out.push({ icon: '🏆', text: `${Math.round(rzShare*100)}% red-zone target share — strong touchdown upside.` })

    if (tag === 'sleeper' && diff != null)
      out.push({ icon: '💎', text: `Being drafted ${diff} spots later than model projects — significant value at current ADP.` })
    else if (tag === 'bust' && diff != null)
      out.push({ icon: '⚠️', text: `Being drafted ${Math.abs(diff)} spots earlier than model projects — overvalued at current ADP.` })

    return out
  }

  function statusColor(status) {
    if (!status || status === 'Active') return null
    if (['IR', 'PUP'].includes(status)) return '#f87171'
    if (['Questionable', 'Doubtful'].includes(status)) return '#facc15'
    return '#9ca3af'
  }
</script>

<div class={SECTION_LABEL}>ADP vs Projection</div>
<div class="flex flex-wrap items-center gap-4 bg-surface border border-border-soft rounded-[10px] p-4 mb-5">
  <div class="flex flex-col items-center bg-surface-deep border border-border-soft rounded-lg px-[1.1rem] py-2.5 min-w-[110px]">
    <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">ADP</span>
    <span class="text-[1.7rem] font-bold text-gray-50 leading-tight">{adp ?? '—'}</span>
    <span class="text-xs text-gray-500">draft pos</span>
  </div>
  <span class="text-gray-500 text-lg">→</span>
  <div class="flex flex-col items-center bg-surface-deep border border-border-soft rounded-lg px-[1.1rem] py-2.5 min-w-[110px]">
    <span class="text-[0.62rem] font-semibold uppercase tracking-wider text-gray-500">EST. ADP</span>
    <span class="text-[1.7rem] font-bold text-gray-50 leading-tight">{player?.estimated_adp ?? '—'}</span>
    <span class="text-xs text-gray-500">our model</span>
  </div>
  <div
    class="flex items-center gap-2 px-4 py-2.5 rounded-lg border font-bold text-sm tracking-wider"
    style="border-color:{tagInfo.border}; background:{tagInfo.bg}; color:{tagInfo.color}"
  >
    <span class="text-base">{tagInfo.icon}</span>
    <span>{tagInfo.label}</span>
  </div>
  {#if tagInfo.sub}
    <div class="ml-auto text-sm font-bold" style="color:{tagInfo.color}">
      <strong>{tagInfo.sub.split(' ')[0]}</strong>
      <span class="text-gray-500 font-medium ml-1">{tagInfo.sub.split(' ').slice(1).join(' ')}</span>
    </div>
  {/if}
</div>

<div class="grid grid-cols-2 gap-3 items-stretch mb-5">
  <div class="flex flex-col min-w-0">
    <div class="flex flex-wrap items-center gap-2 mb-2">
      <span class={SECTION_LABEL.replace('mb-2', 'm-0')}>ADP Trend</span>
      <div class="flex gap-2 ml-auto">
        <span class="flex items-center gap-1 text-gray-500 text-[0.7rem]">
          <span class="w-4 h-0.5 rounded-sm shrink-0 bg-blue-500"></span>Historical
        </span>
        {#if adpHistory?.estimated_adp}
          <span class="flex items-center gap-1 text-gray-500 text-[0.7rem]">
            <span class="w-4 h-0.5 rounded-sm shrink-0" style="background: repeating-linear-gradient(to right, #34d399 0px, #34d399 3px, transparent 3px, transparent 6px)"></span>'26
          </span>
        {/if}
      </div>
    </div>
    {#if adpHistory && (adpHistory.historical?.length > 0 || adpHistory.current_adp)}
      <div class="bg-surface border border-border-soft rounded-lg p-2.5 flex-1 min-h-[220px] relative">
        <canvas bind:this={canvasAdp} class="absolute inset-2.5 !w-[calc(100%-1.25rem)] !h-[calc(100%-1.25rem)]"></canvas>
      </div>
    {:else}
      <div class={EMPTY}>No ADP data available</div>
    {/if}
  </div>

  <div class="flex flex-col min-w-0">
    <span class="{SECTION_LABEL.replace('mb-2', 'mb-2')}">Smart Insights</span>
    {#if insights.length > 0}
      <div class="flex flex-col gap-2 flex-1">
        {#each insights as item}
          <div class="flex items-start gap-3 bg-surface border border-border-soft border-l-[3px] !border-l-emerald-400 rounded-lg px-3.5 py-2.5">
            <span class="text-base shrink-0">{item.icon}</span>
            <span class="text-gray-200 text-[0.88rem] leading-snug">{item.text}</span>
          </div>
        {/each}
      </div>
    {:else}
      <div class={EMPTY}>No insights available</div>
    {/if}
  </div>
</div>

<div class="flex justify-center">
  <div class="w-full max-w-[600px]">
    <span class="block text-center text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">
      {player?.team ?? ''} Depth Chart
    </span>
    {#if depthLoading}
      <div class={EMPTY}>Loading...</div>
    {:else if depthData?.depth_chart}
      <div class="bg-surface border border-border-soft rounded-lg px-2 py-1.5 flex flex-col overflow-hidden">
        {#each POSITION_ORDER as pos}
          {#if depthData.depth_chart[pos]?.length}
            <div class="flex items-start gap-2 px-1 py-1.5 border-b border-border-soft last:border-b-0">
              <div class="min-w-[28px] text-[0.65rem] font-bold text-gray-600 uppercase tracking-wider pt-0.5 shrink-0">{pos}</div>
              <div class="flex flex-col gap-0.5 flex-1 min-w-0">
                {#each depthData.depth_chart[pos] as p}
                  <div class="flex items-center justify-center gap-2 px-1.5 py-0.5 rounded {p.is_current_player ? 'bg-blue-500/[0.08] border border-blue-500/20' : ''}">
                    <span class="text-[0.62rem] font-semibold min-w-[18px] shrink-0 text-right {p.depth_order === 1 ? 'text-yellow-400' : 'text-gray-700'}">
                      #{p.depth_order}
                    </span>
                    <span class="text-xs whitespace-nowrap overflow-hidden text-ellipsis text-center min-w-[120px] {p.is_current_player ? 'text-gray-50 font-semibold' : 'text-gray-400'}">
                      {p.name}
                    </span>
                    {#if p.status && p.status !== 'Active'}
                      <span
                        class="text-[0.6rem] font-semibold uppercase tracking-wider shrink-0 min-w-[80px]"
                        style="color:{statusColor(p.status)}"
                      >
                        {p.status}
                      </span>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        {/each}
      </div>
    {:else}
      <div class={EMPTY}>No depth chart available</div>
    {/if}
  </div>
</div>
