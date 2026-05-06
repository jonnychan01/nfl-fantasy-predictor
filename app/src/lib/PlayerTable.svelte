<script>
  import Modal from '../modal/Modal.svelte'

  export let players = []

  const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF']
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

  let selectedPosition = 'ALL'
  let sortColumn = 'projected_points'
  let sortAsc = false
  let searchQuery = ''
  let selectedPlayer = null
  let visibleCount = 50

  $: filtered = players
    .filter(p => selectedPosition === 'ALL' || p.position === selectedPosition)
    .filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))

  $: sorted = [...filtered].sort((a, b) => {
    const valA = a[sortColumn] ?? ''
    const valB = b[sortColumn] ?? ''
    if (valA < valB) return sortAsc ? -1 : 1
    if (valA > valB) return sortAsc ? 1 : -1
    return 0
  })

  $: paginated = sorted.slice(0, visibleCount)

  function handleSort(col) {
    if (sortColumn === col) {
      sortAsc = !sortAsc
    } else {
      sortColumn = col
      sortAsc = false
    }
  }

  function sortIcon(col) {
    if (sortColumn !== col) return '↕'
    return sortAsc ? '↑' : '↓'
  }
</script>

<svelte:head>
  <style>
    body { background-color: #f3f4f6 !important; }
  </style>
</svelte:head>

<input
  type="text"
  placeholder="Search players..."
  bind:value={searchQuery}
  class="w-full mb-4 px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm outline-none focus:border-blue-500"
/>

<div class="flex flex-wrap justify-center gap-2 mb-4">
  {#each POSITIONS as pos}
    <button
      class="px-4 py-1.5 rounded-full border text-sm transition-colors cursor-pointer
        {selectedPosition === pos
          ? 'bg-blue-500 border-blue-500 text-white'
          : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700 hover:text-gray-50'}"
      on:click={() => selectedPosition = pos}
    >
      {pos}
    </button>
  {/each}
</div>

<div class="overflow-x-auto rounded-lg border border-border-soft">
  <table class="w-full border-collapse text-sm">
    <thead class="bg-border-soft">
      <tr>
        {#each [['name','Name'],['position','POS'],['team','Team'],['age','Age'],['projected_points','Projected Pts'],['estimated_adp','Est. ADP']] as [key, label]}
          <th
            on:click={() => handleSort(key)}
            class="px-4 py-3 text-left font-semibold text-gray-500 cursor-pointer select-none whitespace-nowrap hover:text-gray-900"
          >
            {label} {sortIcon(key)}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
    {#each paginated as player}
      <tr
        on:click={() => selectedPlayer = player}
        class="cursor-pointer bg-white text-gray-900 hover:[&>td]:bg-[#f3f4f6]"
      >
        <td class="px-4 py-2.5 border-t border-border-soft">
          <div class="flex items-center gap-2.5">
            {#if player.position === 'DEF'}
              {#key player.player_id}
              <img
                src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
                alt={player.team}
                class="w-[38px] h-[38px] rounded-full object-cover bg-white"
                loading="lazy"
                on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
              />
              {/key}
            {:else}
              {#key player.player_id}
              <img
                src={`https://sleepercdn.com/content/nfl/players/thumb/${player.player_id}.jpg`}
                alt={player.name}
                class="w-[38px] h-[38px] rounded-full object-cover bg-white"
                loading="lazy"
                on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
              />
              {/key}
            {/if}
            {player.name}
          </div>
        </td>
        <td class="px-4 py-2.5 border-t border-border-soft">
          <span class="px-2 py-0.5 rounded text-xs font-bold {POS_BADGE[player.position] ?? ''}">{player.position}</span>
        </td>
        <td class="px-4 py-2.5 border-t border-border-soft">{player.team ?? '—'}</td>
        <td class="px-4 py-2.5 border-t border-border-soft">{player.age ?? '—'}</td>
        <td class="px-4 py-2.5 border-t border-border-soft font-bold text-emerald-400">
          {player.projected_points}
          {#if player.tag === 'sleeper'}
            <span class="ml-1.5 align-middle text-[0.6rem] font-bold px-1.5 py-0.5 rounded tracking-wider bg-emerald-400/15 text-emerald-400 border border-emerald-400">BOOM</span>
          {:else if player.tag === 'bust'}
            <span class="ml-1.5 align-middle text-[0.6rem] font-bold px-1.5 py-0.5 rounded tracking-wider bg-red-400/15 text-red-400 border border-red-400">BUST</span>
          {/if}
        </td>
        <td class="px-4 py-2.5 border-t border-border-soft">{player.estimated_adp ?? '—'}</td>
      </tr>
    {/each}
  </tbody>
  </table>
    {#if visibleCount < sorted.length}
      <button
        on:click={() => visibleCount += 50}
        class="w-full mt-4 py-2.5 bg-white border border-gray-300 text-gray-600 rounded-lg cursor-pointer hover:bg-gray-100 hover:text-gray-900"
      >
        Load more
      </button>
    {/if}
</div>

{#if selectedPlayer}
  <Modal player={selectedPlayer} onClose={() => selectedPlayer = null} />
{/if}