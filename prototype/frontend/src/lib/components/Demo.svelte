<script lang="ts">
	import { onMount } from 'svelte';
	import Keyboard from './Keyboard.svelte';

	// "Mary had a little lamb, little lamb, little lamb" in C: what the player shows for a real song.
	const PHRASE: [string, number][] = [
		['mi', 64], ['re', 62], ['do', 60], ['re', 62], ['mi', 64], ['mi', 64], ['mi', 64],
		['re', 62], ['re', 62], ['re', 62],
		['mi', 64], ['so', 67], ['so', 67]
	];
	const BREAKS = new Set([7, 10]); // a breath before "little lamb"
	const NAMES: Record<number, string> = { 60: 'C4', 62: 'D4', 64: 'E4', 67: 'G4' };
	const STEP_MS = 520;

	let current = $state(0);

	onMount(() => {
		if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		let timer: ReturnType<typeof setTimeout>;
		const advance = () => {
			current = (current + 1) % (PHRASE.length + 2); // two beats of rest before it loops
			timer = setTimeout(advance, BREAKS.has(current) ? STEP_MS * 1.6 : STEP_MS);
		};
		timer = setTimeout(advance, STEP_MS);
		return () => clearTimeout(timer);
	});
</script>

<figure class="stand">
	<figcaption>do = C</figcaption>
	<ol class="line" aria-label="Mary Had a Little Lamb in tonic solfa">
		{#each PHRASE as [syl, midi], i (i)}
			{#if BREAKS.has(i)}<li class="gap" aria-hidden="true"></li>{/if}
			<li class:now={i === current}>
				<span class="syl solfa">{syl}</span>
				<span class="key">{NAMES[midi]}</span>
			</li>
		{/each}
	</ol>
	<Keyboard range={[60, 71]} active={PHRASE[current]?.[1] ?? null} label="The key to press lights up" />
</figure>

<style>
	.stand {
		margin: 0;
		padding: var(--space-5);
		border-radius: var(--radius-panel);
		background: #1e2350;
		color: #eceef8;
		display: grid;
		gap: var(--space-5);
	}

	figcaption {
		font-size: var(--step--1);
		color: #a9aed0;
	}

	.line {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-1);
	}

	li {
		display: grid;
		justify-items: center;
		padding: var(--space-2) var(--space-2) var(--space-1);
		border-radius: 8px;
		min-width: 2.6em;
	}

	li.gap {
		min-width: var(--space-3);
		padding: 0;
	}

	li.now {
		background: var(--lamp);
		color: var(--lamp-ink);
	}

	.syl {
		font-size: var(--step-2);
		line-height: 1;
	}

	.key {
		font-size: 11px;
		opacity: 0.75;
	}
</style>
