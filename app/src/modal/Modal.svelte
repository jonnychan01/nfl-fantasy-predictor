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

  const POS_BADGE = {
    QB:  'bg-pos-qb-bg text-pos-qb-fg',
    RB:  'bg-pos-rb-bg text-pos-rb-fg',
    WR:  'bg-pos-wr-bg text-pos-wr-fg',
    TE:  'bg-pos-te-bg text-pos-te-fg',
    K:   'bg-pos-k-bg text-pos-k-fg',
    DEF: 'bg-pos-def-bg text-pos-def-fg',
  }

  const TABS = [
    ['overview', 'Overview'],
    ['schedule', 'Schedule'],
    ['history',  'History'],
    ['analysis', 'Analysis'],
  ]

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

<div
  class="fixed inset-0 z-[100] bg-black/60 flex items-center justify-center"
  on:click={onClose}
  on:keydown={(e) => e.key === 'Escape' && onClose()}
  role="button"
  tabindex="0"
>
  <div
    class="bg-surface border border-border rounded-xl p-8 w-[95%] max-w-[1000px] max-h-[90vh] overflow-y-auto"
    on:click|stopPropagation
    on:keydown|stopPropagation
    role="dialog"
    tabindex="-1"
  >
    <div class="flex justify-between items-start mb-4">
      <div class="flex items-center gap-4">
        {#if player.position === 'DEF'}
          <img
            src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
            alt={player.team}
            class="w-20 h-20 rounded-full object-cover border border-border shrink-0"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
        {:else}
          <img
            src={`https://sleepercdn.com/content/nfl/players/thumb/${player.player_id}.jpg`}
            alt={player.name}
            class="w-20 h-20 rounded-full object-cover border border-border shrink-0"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
        {/if}
        <div>
          <h2 class="m-0 mb-1.5 text-gray-50 text-2xl font-medium">{player.name}</h2>
          <span class="px-2 py-0.5 rounded text-xs font-bold {POS_BADGE[player.position] ?? ''}">{player.position}</span>
          <img
            src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
            alt={player.team}
            class="inline w-[18px] h-[18px] object-contain align-middle ml-1 mr-0.5"
            on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
          />
          <span class="text-sm text-gray-400 ml-2">{player.team}</span>
        </div>
        <div class="flex gap-6 pl-6 ml-2 border-l border-border">
          <div class="flex flex-col text-sm text-gray-400">
            <span>Age</span>
            <strong class="text-base text-gray-50 mt-0.5">{player.age ?? '—'}</strong>
          </div>
          <div class="flex flex-col text-sm text-gray-400">
            <span>Experience</span>
            <strong class="text-base text-gray-50 mt-0.5">{player.years_experience}y</strong>
          </div>
          <div class="flex flex-col text-sm text-gray-400">
            <span>Projected</span>
            <strong class="text-base text-gray-50 mt-0.5">{player.projected_points}</strong>
          </div>
        </div>
      </div>
      <button
        class="bg-transparent border-0 text-gray-400 text-lg cursor-pointer p-0"
        on:click={onClose}
      >✕</button>
    </div>

    <div class="flex border-b border-border mb-6">
      {#each TABS as [id, label]}
        <button
          class="bg-transparent border-0 border-b-2 px-5 py-2.5 cursor-pointer text-sm -mb-px transition-colors
            {activeTab === id
              ? 'border-blue-500 text-gray-50'
              : 'border-transparent text-gray-500 hover:text-gray-300'}"
          on:click={() => activeTab = id}
        >{label}</button>
      {/each}
    </div>

    <div class:hidden={activeTab !== 'overview'}>
      <OverviewTab {player} weeklyData={scheduleData?.weeks ?? null} />
    </div>
    <div class:hidden={activeTab !== 'schedule'}>
      <ScheduleTab data={scheduleData} />
    </div>
    <div class:hidden={activeTab !== 'history'}>
      <HistoryTab {player} />
    </div>
    <div class:hidden={activeTab !== 'analysis'}>
      <AnalysisTab {player} />
    </div>

  </div>
</div>
