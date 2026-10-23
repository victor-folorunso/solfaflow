<script lang="ts">
	import { NOTE_NAMES } from '#lib/solfa.ts';

	interface Props {
		/** MIDI pitches the keyboard must include; it is widened to whole octaves from C. */
		range: number[];
		/** The key sounding now (lamp yellow). */
		active?: number | null;
		/** Pitch classes of the current chord, lit softly in the lowest octave. */
		chordTones?: number[];
		label?: string;
	}

	let { range, active = null, chordTones = [], label = 'Keyboard' }: Props = $props();

	const isBlack = (m: number) => NOTE_NAMES[((m % 12) + 12) % 12].includes('#');
	const bounds = $derived.by(() => {
		const pitches = range.length ? range : [60, 71];
		let lo = Math.min(...pitches);
		let hi = Math.max(...pitches);
		lo -= ((lo % 12) + 12) % 12;
		hi += 11 - (((hi % 12) + 12) % 12);
		return { lo, hi };
	});
	const whites = $derived(
		Array.from({ length: bounds.hi - bounds.lo + 1 }, (_, i) => bounds.lo + i).filter((m) => !isBlack(m))
	);
	const chordKeys = $derived(new Set(chordTones.map((pc) => bounds.lo + pc)));
</script>

<div class="keys" role="img" aria-label={label} style:--whites={whites.length}>
	{#each whites as m, i (m)}
		<div class="white" class:on={active === m} class:chord={chordKeys.has(m)} style:--i={i}>
			{#if m % 12 === 0}<span>C{m / 12 - 1}</span>{/if}
		</div>
		{#if m + 1 <= bounds.hi && isBlack(m + 1)}
			<div class="black" class:on={active === m + 1} class:chord={chordKeys.has(m + 1)} style:--i={i + 1}></div>
		{/if}
	{/each}
</div>

<style>
	.keys {
		position: relative;
		height: 84px;
		max-width: calc(var(--whites) * 44px);
		touch-action: manipulation;
	}

	.white,
	.black {
		position: absolute;
		top: 0;
		border-radius: 0 0 6px 6px;
		transition: background-color 60ms linear;
	}

	.white {
		left: calc(var(--i) * 100% / var(--whites));
		width: calc(100% / var(--whites));
		height: 100%;
		background: var(--ivory);
		border: 1px solid #c9cbdb;
	}

	.black {
		left: calc(var(--i) * 100% / var(--whites) - 100% / var(--whites) * 0.3);
		width: calc(100% / var(--whites) * 0.6);
		height: 58%;
		background: #1b1d33;
		z-index: 1;
	}

	.white.chord {
		background: #dfe3ff;
	}

	.black.chord {
		background: #4b55a8;
	}

	.white.on,
	.black.on {
		background: var(--lamp);
	}

	span {
		position: absolute;
		bottom: 4px;
		width: 100%;
		text-align: center;
		font-size: 10px;
		color: #6b6f8c;
	}
</style>
