<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { page } from '$app/state';
	import { getJob, getResult, resultUrl } from '#lib/api.ts';
	import Keyboard from '#lib/components/Keyboard.svelte';
	import Seo from '#lib/components/Seo.svelte';
	import {
		NOTE_NAMES,
		activeIndex,
		chordName,
		chordNumeral,
		chordTones,
		displayPitches,
		exactPitch,
		formatTime,
		homeDo,
		isComplete,
		keyName,
		layoutSheet,
		syllable,
		transposeShift,
		type SolfaResult
	} from '#lib/solfa.ts';

	const POLL_MS = 3000;
	const id = $derived(page.params.id ?? '');

	let result = $state<SolfaResult | null>(null);
	let title = $state('');
	let loadError = $state('');

	// Player settings.
	let doPc = $state<number | null>(null);
	let userDo = $state(false);
	let hear = $state<'song' | 'synth' | 'both'>('both');
	let exact = $state(false);
	let showChords = $state(true);
	let toC = $state(false);
	let rate = $state(1);

	// Playback.
	let song = $state<HTMLAudioElement>();
	let synth = $state<HTMLAudioElement>();
	let now = $state(0);
	let duration = $state(0);
	let playing = $state(false);
	let keyNotice = $state('');
	let sheet = $state<HTMLElement>();

	const notes = $derived(result?.notes ?? []);
	const chords = $derived(showChords ? (result?.chords ?? []) : []);
	const shift = $derived(transposeShift(doPc, toC));
	const pitches = $derived(result ? displayPitches(result, doPc, exact) : []);
	const home = $derived(homeDo(notes, doPc));
	const phrases = $derived(layoutSheet(notes, chords));
	const current = $derived(activeIndex(notes, now));
	const currentChord = $derived(chords[activeIndex(chords, now)] ?? null);
	const complete = $derived(result ? isComplete(result) : false);
	const processed = $derived(result?.processed_seconds ?? 0);
	const total = $derived(result?.duration || duration || 0);
	const ahead = $derived(!complete && now > processed && result !== null);

	function apply(next: SolfaResult) {
		const previous = doPc;
		result = next;
		if (!userDo) {
			doPc = next.do_pitch_class;
			if (previous !== null && doPc !== null && doPc !== previous) {
				keyNotice = `Key updated to do = ${NOTE_NAMES[doPc]} now that more of the song is done. You can change it below.`;
				setTimeout(() => (keyNotice = ''), 12000);
			}
		}
	}

	onMount(() => {
		let stopped = false;
		let timer: ReturnType<typeof setTimeout>;
		getJob(id)
			.then((job) => (title = job.name))
			.catch(() => (title = 'Your song'));
		const poll = async () => {
			try {
				const next = await getResult(id);
				if (!result || (next.version ?? 0) > (result.version ?? 0)) apply(next);
				loadError = '';
			} catch (e) {
				if (!result) loadError = 'This song could not be found. It may have been removed.';
			}
			if (!stopped && !(result && isComplete(result))) timer = setTimeout(poll, POLL_MS);
		};
		poll();
		let frame = requestAnimationFrame(function loop() {
			if (song) {
				now = song.currentTime;
				if (synth && !song.paused && Math.abs(synth.currentTime - now) > 0.08) synth.currentTime = now;
			}
			frame = requestAnimationFrame(loop);
		});
		return () => {
			stopped = true;
			clearTimeout(timer);
			cancelAnimationFrame(frame);
		};
	});

	// Swap in the newest synth track without losing the place.
	$effect(() => {
		if (!synth || !result?.synth_file) return;
		const src = resultUrl(id, result.synth_file);
		if (synth.src.endsWith(src)) return;
		const wasPlaying = song ? !song.paused : false;
		synth.src = src;
		synth.onloadedmetadata = () => {
			if (!synth || !song) return;
			synth.currentTime = song.currentTime;
			synth.playbackRate = rate;
			if (wasPlaying && !song.paused) synth.play();
		};
	});

	$effect(() => {
		if (song) song.muted = hear === 'synth';
		if (synth) synth.muted = hear === 'song';
	});

	$effect(() => {
		if (song) song.playbackRate = rate;
		if (synth) synth.playbackRate = rate;
	});

	// Keep the current syllable in view while playing.
	$effect(() => {
		if (current < 0 || !playing || !sheet) return;
		tick().then(() => {
			const el = sheet?.querySelector<HTMLElement>(`[data-note="${current}"]`);
			if (!el) return;
			const box = el.getBoundingClientRect();
			if (box.top < 260 || box.bottom > innerHeight - 40) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
		});
	});

	function toggle() {
		if (!song) return;
		if (song.paused) {
			if (synth) synth.currentTime = song.currentTime;
			song.play();
			synth?.play();
		} else {
			song.pause();
			synth?.pause();
		}
	}

	function seek(t: number) {
		if (song) song.currentTime = t;
		if (synth) synth.currentTime = t;
		now = t;
	}

	function onKey(e: KeyboardEvent) {
		const target = e.target as HTMLElement;
		if (e.code === 'Space' && !['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA'].includes(target.tagName)) {
			e.preventDefault();
			toggle();
		}
	}

	const keyEvidence = $derived(
		(result as (SolfaResult & { key_evidence?: string }) | null)?.key_evidence === 'melody + chords'
			? 'the tune and the chords'
			: 'the tune'
	);
	const otherKeys = $derived(
		(result?.key_candidates ?? []).filter((c) => c.do_pitch_class !== doPc).map((c) => c.do)
	);
	const keyRange = $derived(pitches.map((p) => p + shift));
	const SPEED_NAMES: Record<number, string> = { 0.5: 'half speed', 0.75: 'three-quarter speed', 1: 'normal speed' };
	const settingsSummary = $derived(
		[doPc === null ? null : `do = ${NOTE_NAMES[doPc]}`, SPEED_NAMES[rate], hear === 'song' ? 'song only' : hear === 'synth' ? 'notes only' : null]
			.filter(Boolean)
			.join(', ')
	);
</script>

<svelte:window onkeydown={onKey} />
<Seo title={title || 'Your song'} description="Tonic solfa for this song." path="/songs/{id}" noindex />

{#if loadError}
	<div class="wrap empty">
		<h1>Song not found</h1>
		<p>{loadError} <a href="/songs">See your songs</a>.</p>
	</div>
{:else}
	<audio bind:this={song} src={resultUrl(id, 'song.wav')} preload="auto" bind:duration
		onplay={() => (playing = true)} onpause={() => (playing = false)}></audio>
	<audio bind:this={synth} preload="auto"></audio>

	<section class="deck">
		<div class="wrap">
			<div class="head">
				<a class="back" href="/songs">Your songs</a>
				<h1>{title}</h1>
			</div>

			<div class="transport">
				<button class="play" onclick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
					{#if playing}
						<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg>
					{:else}
						<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" /></svg>
					{/if}
				</button>
				<div class="scrub">
					<input type="range" min="0" max={total || 0} step="0.01" value={now}
						oninput={(e) => seek(+e.currentTarget.value)} aria-label="Position in the song" />
					{#if !complete && total}
						<div class="ready" title="How much of the song has solfa so far">
							<i style:width="{(100 * processed) / total}%"></i>
						</div>
					{/if}
				</div>
				<span class="clock">{formatTime(now)} / {formatTime(total)}</span>
			</div>

			<Keyboard
				range={keyRange}
				active={current >= 0 ? pitches[current] + shift : null}
				chordTones={currentChord ? chordTones(currentChord).map((pc) => (pc + shift + 12) % 12) : []}
				label="The key to press now"
			/>

			{#if keyNotice || ahead}
				<p class="notice" role="status">
					{ahead
						? `You're ahead of the transcription. The solfa is ready up to ${formatTime(processed)}; the rest is on its way.`
						: keyNotice}
				</p>
			{/if}
		</div>
	</section>

	<div class="wrap">
		<details class="settings-panel">
			<summary>Settings <span>{settingsSummary}</span></summary>
			<div class="settings">
				<label class="field">
					Hear
					<select bind:value={hear}>
						<option value="both">Song and notes</option>
						<option value="song">The song only</option>
						<option value="synth">Notes only</option>
					</select>
				</label>
				<label class="field">
					Key
					<select value={doPc ?? ''} onchange={(e) => { doPc = +e.currentTarget.value; userDo = true; keyNotice = ''; }}>
						{#if doPc === null}<option value="">Not known yet</option>{/if}
						{#each NOTE_NAMES as name, pc (name)}<option value={pc}>do = {name}</option>{/each}
					</select>
				</label>
				<label class="field">
					Key names
					<select bind:value={toC}>
						<option value={false}>As recorded</option>
						<option value={true}>Moved so do = C</option>
					</select>
				</label>
				<label class="field">
					Notes
					<select bind:value={exact}>
						<option value={false}>Slides cleaned up</option>
						<option value={true}>Exact, as sung</option>
					</select>
				</label>
				<label class="field">
					Chords
					<select bind:value={showChords}>
						<option value={true}>Show</option>
						<option value={false}>Hide</option>
					</select>
				</label>
				<label class="field">
					Speed
					<select bind:value={rate}>
						<option value={0.5}>Half</option>
						<option value={0.75}>Three quarters</option>
						<option value={1}>Normal</option>
					</select>
				</label>
			</div>
		</details>

		{#if doPc !== null}
			<p class="keyline">
				{#if userDo}
					You set do = {NOTE_NAMES[doPc]}.
				{:else}
					do = {NOTE_NAMES[doPc]}, worked out from {keyEvidence}{complete ? '' : ' so far'}.
					{#if otherKeys.length}If it sounds wrong, try do = {otherKeys.join(' or ')}.{/if}
				{/if}
			</p>
		{/if}

		<div class="sheet" bind:this={sheet}>
			{#each phrases as phrase, p (p)}
				<div class="phrase">
					<button class="time" onclick={() => seek(phrase.start)}>{formatTime(phrase.start)}</button>
					<div class="items">
						{#each phrase.items as item, k (k)}
							{#if item.kind === 'rest'}
								<span class="rest" aria-label="rest">–</span>
							{:else if item.kind === 'chord'}
								<button class="chip" onclick={() => seek(item.chord.start)} class:now={item.chord === currentChord}>
									<b>{chordName(item.chord, shift)}</b>
									<span>{chordNumeral(item.chord, doPc)}</span>
								</button>
							{:else}
								{@const n = notes[item.index]}
								{@const { syl, mark } = syllable(pitches[item.index], home)}
								{@const cleaned = pitches[item.index] !== exactPitch(n)}
								<button class="note" data-note={item.index} class:now={item.index === current} class:cleaned
									onclick={() => seek(n.start)}
									title={cleaned ? `Sung as ${keyName(exactPitch(n), shift)}; written as the note the singer was aiming for` : undefined}>
									{#if chords.length}
										<span class="chord">
											{#if item.chordAbove}<b>{chordName(item.chordAbove, shift)}</b> {chordNumeral(item.chordAbove, doPc)}{/if}
										</span>
									{/if}
									<span class="syl solfa">{syl}<span class="mark">{mark}</span></span>
									<span class="dur" style:width="{Math.min(56, 8 + (n.end - n.start) * 40)}px"></span>
									<span class="key">{keyName(pitches[item.index], shift)}</span>
								</button>
							{/if}
						{/each}
					</div>
				</div>
			{/each}

			{#if result && !complete}
				<p class="pending">
					{#if notes.length}
						Working out the notes after {formatTime(processed)}…
					{:else if processed > 0}
						No singing found up to {formatTime(processed)}, probably an instrumental intro. Working on the next part…
					{:else}
						Working out the first notes. You can play the song already.
					{/if}
				</p>
			{:else if result === null}
				<p class="pending">Loading…</p>
			{/if}
		</div>
	</div>
{/if}

<style>
	.deck {
		position: sticky;
		top: 0;
		z-index: 2;
		background: var(--paper);
		border-bottom: 1px solid var(--rule);
		padding: var(--space-4) 0;
	}

	.deck .wrap {
		display: grid;
		gap: var(--space-4);
	}

	.head {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: var(--space-2) var(--space-4);
	}

	.back {
		color: var(--slate);
		font-size: var(--step--1);
	}

	h1 {
		font-size: var(--step-2);
		margin: 0;
		overflow-wrap: anywhere;
	}

	.transport {
		display: flex;
		align-items: center;
		gap: var(--space-4);
	}

	.play {
		flex: none;
		width: 56px;
		height: 56px;
		border-radius: 50%;
		border: 0;
		background: var(--indigo);
		color: #fff;
		display: grid;
		place-items: center;
		cursor: pointer;
	}

	.play svg {
		width: 26px;
		height: 26px;
		fill: currentColor;
	}

	@media (prefers-color-scheme: dark) {
		.play {
			color: #12152e;
		}
	}

	.scrub {
		flex: 1;
		display: grid;
		gap: 4px;
	}

	.scrub input {
		width: 100%;
		accent-color: var(--indigo);
	}

	.ready {
		height: 4px;
		border-radius: 2px;
		background: var(--rule);
		overflow: hidden;
	}

	.ready i {
		display: block;
		height: 100%;
		background: var(--indigo);
		opacity: 0.5;
		transition: width 0.4s;
	}

	.clock {
		font-variant-numeric: tabular-nums;
		color: var(--slate);
		font-size: var(--step--1);
		white-space: nowrap;
	}

	.settings-panel {
		margin-top: var(--space-4);
		border-bottom: 1px solid var(--rule);
		padding-bottom: var(--space-3);
	}

	.settings-panel summary {
		cursor: pointer;
		font-weight: 700;
		padding: var(--space-2) 0;
		width: max-content;
		max-width: 100%;
	}

	.settings-panel summary span {
		font-weight: 400;
		color: var(--slate);
		margin-left: var(--space-2);
	}

	.settings {
		padding-top: var(--space-3);
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr));
		gap: var(--space-3);
	}

	.notice {
		margin: 0;
		padding: var(--space-3) var(--space-4);
		border-radius: var(--radius-control);
		background: var(--indigo-soft);
		font-size: var(--step--1);
	}

	.keyline {
		color: var(--slate);
		margin: var(--space-5) 0 var(--space-2);
	}

	.phrase {
		display: grid;
		grid-template-columns: 3.5rem 1fr;
		gap: var(--space-3);
		padding: var(--space-4) 0;
		border-bottom: 1px solid var(--rule);
	}

	.time {
		align-self: start;
		margin-top: 1.6rem;
		padding: 0;
		border: 0;
		background: none;
		color: var(--slate);
		font-size: var(--step--1);
		font-variant-numeric: tabular-nums;
		cursor: pointer;
		text-align: left;
	}

	.items {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: var(--space-1);
	}

	.note {
		display: grid;
		justify-items: center;
		gap: 2px;
		min-width: 2.75rem;
		padding: var(--space-1) var(--space-2) var(--space-2);
		border: 0;
		border-radius: 10px;
		background: none;
		color: inherit;
		cursor: pointer;
	}

	.note:hover {
		background: var(--indigo-soft);
	}

	.note.now {
		background: var(--lamp);
		color: var(--lamp-ink);
	}

	.chord {
		min-height: 1.2em;
		font-size: var(--step--1);
		color: var(--indigo);
		white-space: nowrap;
	}

	.note.now .chord {
		color: var(--lamp-ink);
	}

	.syl {
		font-size: var(--step-2);
		line-height: 1.05;
	}

	.cleaned .syl {
		text-decoration: underline dotted;
		text-decoration-thickness: 2px;
		text-underline-offset: 5px;
	}

	.mark {
		font-size: 0.7em;
	}

	.dur {
		height: 3px;
		border-radius: 2px;
		background: currentColor;
		opacity: 0.35;
	}

	.key {
		font-size: 12px;
		color: var(--slate);
	}

	.note.now .key {
		color: var(--lamp-ink);
	}

	.rest {
		align-self: center;
		padding: 0 var(--space-1);
		color: var(--slate);
		font-size: var(--step-1);
	}

	.chip {
		align-self: center;
		padding: var(--space-1) var(--space-3);
		border: 1.5px solid var(--rule);
		border-radius: 999px;
		background: var(--surface);
		color: var(--indigo);
		cursor: pointer;
	}

	.chip span {
		color: var(--slate);
		font-size: var(--step--1);
		margin-left: 2px;
	}

	.chip.now {
		border-color: var(--lamp);
		background: var(--lamp);
		color: var(--lamp-ink);
	}

	.pending {
		color: var(--slate);
		font-style: italic;
		padding: var(--space-5) 0;
	}

	.empty {
		padding-top: var(--space-7);
	}

	@media (max-width: 40rem) {
		.settings {
			grid-template-columns: 1fr 1fr;
		}

		.phrase {
			grid-template-columns: 1fr;
			gap: var(--space-1);
		}

		.time {
			margin-top: 0;
		}

		.syl {
			font-size: var(--step-1);
		}
	}
</style>
