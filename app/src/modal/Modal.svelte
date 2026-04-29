<script>
  import { onMount } from 'svelte'
  import OverviewTab from './tabs/OverviewTab.svelte'
  import ScheduleTab from './tabs/ScheduleTab.svelte'
  import HistoryTab from './tabs/HistoryTab.svelte'
  import AnalysisTab from './tabs/AnalysisTab.svelte'

  export let player
  export let onClose

  let scheduleData = null
  let activeTab = 'overview'

  const PLACEHOLDER = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='38' height='38' 
  viewBox='0 0 38 38'%3E%3Ccircle cx='19' cy='19' r='19' fill='%23ffffff'/%3E%3Ccircle cx='19' cy='15' r='7' 
  fill='%239ca3af'/%3E%3Cellipse cx='19' cy='32' rx='12' ry='8' fill='%239ca3af'/%3E%3C/svg%3E`

  onMount(async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/players/${player.player_id}/schedule-projections`)
      scheduleData = await res.json()
    } catch (e) {
      console.error('Failed to fetch schedule:', e)
      scheduleData = null
    }
  })
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
      <div style="display: flex; align-items: center; gap: 1rem;">
        {#if player.position === 'DEF'}
          <img
            src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
            alt={player.team}
            class="player-face"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
        {:else}
          <img
            src={`https://sleepercdn.com/content/nfl/players/thumb/${player.player_id}.jpg`}
            alt={player.name}
            class="player-face"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
        {/if}
        <div>
          <h2>{player.name}</h2>
          <span class="pos-badge {player.position}">{player.position}</span>
          <img
            src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
            alt={player.team}
            class="team-logo-inline"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
          <span class="team">{player.team}</span>
        </div>
        <div class="stats">
          <div class="stat"><span>Age</span><strong>{player.age ?? '—'}</strong></div>
          <div class="stat"><span>Experience</span><strong>{player.years_experience}y</strong></div>
          <div class="stat"><span>Projected</span><strong class="pts">{player.projected_points}</strong></div>
        </div>
      </div>
      <button class="close" on:click={onClose}>✕</button>
    </div>

    <div class="tab-bar">
      <button class:active={activeTab === 'overview'} on:click={() => activeTab = 'overview'}>Overview</button>
      <button class:active={activeTab === 'schedule'} on:click={() => activeTab = 'schedule'}>Schedule</button>
      <button class:active={activeTab === 'history'} on:click={() => activeTab = 'history'}>History</button>
      <button class:active={activeTab === 'analysis'} on:click={() => activeTab = 'analysis'}>Analysis</button>
    </div>

    <div style={activeTab === 'overview' ? '' : 'display: none'}>
      <OverviewTab {player} weeklyData={scheduleData?.weeks ?? null} />
    </div>
    <div style={activeTab === 'schedule' ? '' : 'display: none'}>
      <ScheduleTab data={scheduleData} />
    </div>
    <div style={activeTab === 'history' ? '' : 'display: none'}>
      <HistoryTab {player} />
    </div>
    <div style={activeTab === 'analysis' ? '' : 'display: none'}>
      <AnalysisTab />
    </div>

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
    padding-left: 1.5rem;
    border-left: 1px solid #374151;
    margin-left: 0.5rem;
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

  .pts { color: #f9fafb !important; }

  .pos-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  .tab-bar {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #374151;
    margin-bottom: 1.5rem;
  }

  .tab-bar button {
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: #6b7280;
    padding: 0.6rem 1.2rem;
    cursor: pointer;
    font-size: 0.85rem;
    margin-bottom: -1px;
    transition: all 0.2s;
  }

  .tab-bar button.active {
    color: #f9fafb;
    border-bottom-color: #3b82f6;
  }

  .player-face {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid #374151;
    flex-shrink: 0;
  }

  .team-logo-inline {
    width: 18px;
    height: 18px;
    object-fit: contain;
    vertical-align: middle;
    margin-left: 0.25rem;
    margin-right: 0.1rem;
  }

  .pos-badge.QB  { background: #2d0a1e; color: #fc2b6d; }
  .pos-badge.RB  { background: #0a2420; color: #20ceb8; }
  .pos-badge.WR  { background: #0f1f35; color: #59a7ff; }
  .pos-badge.TE  { background: #2d1a08; color: #feae58; }
  .pos-badge.K   { background: #1e0a2d; color: #c96cff; }
  .pos-badge.DEF { background: #2d1508; color: #bf5f40; }
</style>