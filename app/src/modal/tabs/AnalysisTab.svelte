<script>
  export let player

  const TEAMS = [
    'ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN',
    'DET','GB','HOU','IND','JAX','KC','LAC','LAR','LV','MIA',
    'MIN','NE','NO','NYG','NYJ','PHI','PIT','SF','SEA','TB','TEN','WAS',
  ]

  $: seasons = Object.keys(player?.seasons ?? {}).sort()
  $: latest = player?.seasons?.[seasons[seasons.length - 1]] ?? {}

  $: adp = player?.adp ?? null
  $: rank = player?.projected_rank ?? null
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

  $: baseWeekly = player?.projected_points != null
    ? (player.projected_points / 17).toFixed(1)
    : '—'

  let opponent = ''
  let weekly = null
  let weeklyLoading = false

  $: if (opponent) {
    fetchWeekly(opponent, player?.player_id)
  } else {
    weekly = null
  }

  async function fetchWeekly(opp, pid) {
    if (!pid || !opp) return
    weeklyLoading = true
    try {
      const res = await fetch(`http://localhost:8000/api/players/${pid}/weekly?opponent=${opp}`)
      weekly = await res.json()
    } catch (e) {
      console.error('Weekly projection fetch failed:', e)
      weekly = null
    } finally {
      weeklyLoading = false
    }
  }

  function getTagInfo(tag, d) {
    if (tag === 'sleeper') {
      return { label: 'SLEEPER', color: '#34d399', bg: 'rgba(52, 211, 153, 0.08)', border: '#10b981', icon: '💎', sub: d != null ? `+${d} spots of value` : '' }
    }
    if (tag === 'bust') {
      return { label: 'BUST', color: '#f87171', bg: 'rgba(248, 113, 113, 0.08)', border: '#dc2626', icon: '⚠️', sub: d != null ? `${d} spots of value` : '' }
    }
    return { label: 'FAIR VALUE', color: '#9ca3af', bg: 'rgba(156, 163, 175, 0.08)', border: '#6b7280', icon: '⚖️', sub: d != null ? `${d > 0 ? '+' : ''}${d} spots` : '' }
  }

  function buildInsights({ position, tag, diff, targetShare, snapPct, rzShare }) {
    const out = []
    const skill = ['WR','TE','RB'].includes(position)

    if (skill && targetShare >= 0.25) {
      out.push({ icon: '🎯', text: `Elite target share of ${Math.round(targetShare * 100)}% — likely the clear WR1 on his team.` })
    } else if (skill && targetShare >= 0.18) {
      out.push({ icon: '🎯', text: `Strong target share of ${Math.round(targetShare * 100)}% — featured in the passing game.` })
    } else if (skill && targetShare > 0 && targetShare < 0.10) {
      out.push({ icon: '🎯', text: `Low target share of ${Math.round(targetShare * 100)}% — secondary option in the offense.` })
    }

    if (position !== 'K' && position !== 'DEF' && snapPct >= 0.85) {
      out.push({ icon: '⚡', text: `${Math.round(snapPct * 100)}% snap rate — an every-down player with maximum opportunity.` })
    } else if (position !== 'K' && position !== 'DEF' && snapPct > 0 && snapPct <= 0.40) {
      out.push({ icon: '⚡', text: `${Math.round(snapPct * 100)}% snap rate — limited role on offense.` })
    }

    if (skill && rzShare >= 0.20) {
      out.push({ icon: '🏆', text: `${Math.round(rzShare * 100)}% red-zone target share — strong touchdown upside.` })
    }

    if (tag === 'sleeper' && diff != null) {
      out.push({ icon: '💎', text: `Being drafted ${diff} spots later than model projects — significant value at current ADP.` })
    } else if (tag === 'bust' && diff != null) {
      out.push({ icon: '⚠️', text: `Being drafted ${Math.abs(diff)} spots earlier than model projects — overvalued at current ADP.` })
    }

    return out
  }
</script>

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

<div class="section-label" style="margin-top:1.25rem">Weekly Matchup Projection</div>
<select bind:value={opponent} class="opp-select">
  <option value="">— Select opponent —</option>
  {#each TEAMS.filter(t => t !== player?.team) as t}
    <option value={t}>{t}</option>
  {/each}
</select>

<div class="weekly-grid">
  <div class="weekly-card">
    <span class="cell-label">BASE / WEEK</span>
    <span class="cell-value">{baseWeekly}</span>
  </div>
  {#if opponent && weekly && !weekly.error}
    <div class="weekly-card">
      <span class="cell-label">VS {opponent}</span>
      <span class="cell-value" style="color:{
        weekly.matchup_quality === 'favorable' ? '#34d399'
        : weekly.matchup_quality === 'unfavorable' ? '#f87171'
        : '#facc15'
      }">{weekly.adjusted_projection}</span>
      <span class="cell-sub">{weekly.matchup_quality}</span>
    </div>
    <div class="weekly-card">
      <span class="cell-label">MULTIPLIER</span>
      <span class="cell-value sm">{weekly.opponent_multiplier}x</span>
      <span class="cell-sub">def rating {weekly.opponent_defense_rating}</span>
    </div>
  {:else if weeklyLoading}
    <div class="weekly-card empty">Loading...</div>
  {/if}
</div>

<style>
  .section-label {
    color: #9ca3af;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.5rem;
  }

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

  .cell-value.sm { font-size: 1.15rem; }

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

  .opp-select {
    width: 100%;
    background: #0b1220;
    border: 1px solid #374151;
    color: #f9fafb;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    font-size: 0.95rem;
    margin-bottom: 0.6rem;
  }

  .weekly-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
  }

  .weekly-card {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 0.75rem;
  }

  .weekly-card.empty {
    align-items: center;
    justify-content: center;
    color: #6b7280;
    font-size: 0.85rem;
  }
</style>