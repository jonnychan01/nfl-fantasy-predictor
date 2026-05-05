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

  // ── ADP chart ────────────────────────────────────────────────
  let canvasAdp
  let adpChart = null
  let adpHistory = null

  // ── Depth chart ──────────────────────────────────────────────
  let depthData = null
  let depthLoading = false

  const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

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
        maintainAspectRatio: true,
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

  // ── Helpers ──────────────────────────────────────────────────
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

<!-- ── ADP vs Projection ─────────────────────────────────────── -->
<div class="section-label">ADP vs Projection</div>
<div class="adp-card">
  <div class="adp-cell">
    <span class="cell-label">ADP</span>
    <span class="cell-value">{adp ?? '—'}</span>
    <span class="cell-sub">draft pos</span>
  </div>
  <span class="arrow">→</span>
  <div class="adp-cell">
    <span class="cell-label">EST. ADP</span>
    <span class="cell-value">{player?.estimated_adp ?? '—'}</span>
    <span class="cell-sub">our model</span>
  </div>
  <div class="tier-badge" style="border-color:{tagInfo.border}; background:{tagInfo.bg}; color:{tagInfo.color}">
    <span class="tier-icon">{tagInfo.icon}</span>
    <span class="tier-label">{tagInfo.label}</span>
  </div>
  {#if tagInfo.sub}
    <div class="tier-sub" style="color:{tagInfo.color}">
      <strong>{tagInfo.sub.split(' ')[0]}</strong>
      <span class="muted">{tagInfo.sub.split(' ').slice(1).join(' ')}</span>
    </div>
  {/if}
</div>

<!-- ── ADP Chart + Depth Chart side by side ─────────────────── -->
<div class="side-by-side" style="margin-top:1.25rem">

  <!-- ADP Trend -->
  <div class="side-panel">
    <div class="trend-header">
      <span class="section-label" style="margin:0">ADP Trend</span>
      <div class="legend">
        <span class="legend-item"><span class="dot blue"></span>Historical</span>
        {#if adpHistory?.estimated_adp}
          <span class="legend-item"><span class="dot green"></span>'26</span>
        {/if}
      </div>
    </div>
    {#if adpHistory && (adpHistory.historical?.length > 0 || adpHistory.current_adp)}
      <div class="chart-box">
        <canvas bind:this={canvasAdp}></canvas>
      </div>
    {:else}
      <div class="depth-empty">No ADP data available</div>
    {/if}
  </div>

  <!-- Depth Chart -->
  <div class="side-panel">
    <span class="section-label" style="margin-bottom:0.5rem; display:block">
      {player?.team ?? ''} Depth Chart
    </span>
    {#if depthLoading}
      <div class="depth-empty">Loading...</div>
    {:else if depthData?.depth_chart}
      <div class="depth-card">
        {#each POSITION_ORDER as pos}
          {#if depthData.depth_chart[pos]?.length}
            <div class="depth-group">
              <div class="depth-pos-label">{pos}</div>
              <div class="depth-players">
                {#each depthData.depth_chart[pos] as p}
                  <div class="depth-row" class:depth-highlighted={p.is_current_player}>
                    <span class="depth-order" class:depth-order-1={p.depth_order === 1}>
                      #{p.depth_order}
                    </span>
                    <span class="depth-name" class:depth-name-active={p.is_current_player}>
                      {p.name}
                    </span>
                    {#if p.status && p.status !== 'Active'}
                      <span class="depth-status" style="color:{statusColor(p.status)}">
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
      <div class="depth-empty">No depth chart available</div>
    {/if}
  </div>

</div>

<!-- ── Smart Insights ────────────────────────────────────────── -->
{#if insights.length > 0}
  <div class="section-label" style="margin-top:1.25rem">Smart Insights</div>
  <div class="insights">
    {#each insights as item}
      <div class="insight">
        <span class="insight-icon">{item.icon}</span>
        <span class="insight-text">{item.text}</span>
      </div>
    {/each}
  </div>
{/if}

<style>
  .section-label {
    color: #9ca3af;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.5rem;
  }

  /* ── ADP card ── */
  .adp-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 1rem;
    flex-wrap: wrap;
  }

  .adp-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 0.65rem 1.1rem;
    min-width: 110px;
  }

  .arrow { color: #6b7280; font-size: 1.1rem; }

  .cell-label {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #6b7280;
  }

  .cell-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #f9fafb;
    line-height: 1.1;
  }

  .cell-sub { font-size: 0.7rem; color: #6b7280; }

  .tier-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.65rem 1rem;
    border-radius: 8px;
    border: 1px solid;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.07em;
  }

  .tier-icon { font-size: 1rem; }

  .tier-sub {
    margin-left: auto;
    font-size: 0.85rem;
    font-weight: 700;
  }

  .tier-sub .muted {
    color: #6b7280;
    font-weight: 500;
    margin-left: 0.25rem;
  }

  /* ── Side by side layout ── */
  .side-by-side {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    align-items: start;
  }

  .side-panel {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  /* ── ADP chart ── */
  .trend-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }

  .legend {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    color: #6b7280;
    font-size: 0.7rem;
  }

  .dot {
    width: 16px;
    height: 2px;
    border-radius: 1px;
    flex-shrink: 0;
  }

  .dot.blue { background: #3b82f6; }
  .dot.green {
    background: repeating-linear-gradient(
      to right,
      #34d399 0px, #34d399 3px,
      transparent 3px, transparent 6px
    );
  }

  .chart-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 0.6rem;
  }

  /* ── Depth chart ── */
  .depth-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 0.4rem 0.5rem;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .depth-group {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.3rem 0.2rem;
    border-bottom: 1px solid #1f2937;
  }

  .depth-group:last-child { border-bottom: none; }

  .depth-pos-label {
    min-width: 28px;
    font-size: 0.65rem;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding-top: 0.1rem;
    flex-shrink: 0;
  }

  .depth-players {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    flex: 1;
    min-width: 0;
  }

  .depth-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
  }

  .depth-highlighted {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.2);
  }

  .depth-order {
    font-size: 0.62rem;
    font-weight: 600;
    color: #374151;
    min-width: 18px;
    flex-shrink: 0;
  }

  .depth-order-1 { color: #facc15; }

  .depth-name {
    font-size: 0.75rem;
    color: #9ca3af;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
  }

  .depth-name-active {
    color: #f9fafb;
    font-weight: 600;
  }

  .depth-status {
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    flex-shrink: 0;
  }

  .depth-empty {
    color: #4b5563;
    font-size: 0.8rem;
    padding: 0.75rem 0.25rem;
  }

  /* ── Insights ── */
  .insights {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .insight {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #111827;
    border: 1px solid #1f2937;
    border-left: 3px solid #34d399;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
  }

  .insight-icon { font-size: 1.05rem; }
  .insight-text { color: #e5e7eb; font-size: 0.88rem; }
</style>