<script>
  export let player
  export let weeklyData

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
</script>

{#if weeklyData && weeklyData.length > 0}
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
</style>