<script lang="ts">
	import { goto } from '$app/navigation';
	import { uploadSong } from '#lib/api.ts';
	import { NOTE_NAMES } from '#lib/solfa.ts';

	const MAX_MB = 60;
	const ACCEPT = 'audio/*,.mp3,.wav,.m4a,.aac,.ogg,.opus,.flac,.webm,.mp4';

	let file = $state<File | null>(null);
	let seconds = $state(0);
	let doKey = $state('');
	let voiceOnly = $state(false);
	let dragging = $state(false);
	let uploading = $state(false);
	let error = $state('');
	let input: HTMLInputElement;

	function choose(f: File | null | undefined) {
		error = '';
		if (f && f.size > MAX_MB * 1024 * 1024) {
			error = `That file is ${(f.size / 1048576).toFixed(0)} MB. The limit is ${MAX_MB} MB.`;
			return;
		}
		file = f ?? null;
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		if (!file) return;
		uploading = true;
		error = '';
		try {
			const job = await uploadSong(file, { seconds, do: doKey, voiceOnly });
			await goto(`/songs/${job.id}`);
		} catch (e) {
			error = `Upload failed: ${(e as Error).message}`;
			uploading = false;
		}
	}
</script>

<form onsubmit={submit} class="upload">
	<label
		class="drop"
		class:dragging
		class:chosen={file}
		ondragenter={(e) => {
			e.preventDefault();
			dragging = true;
		}}
		ondragover={(e) => e.preventDefault()}
		ondragleave={() => (dragging = false)}
		ondrop={(e) => {
			e.preventDefault();
			dragging = false;
			choose(e.dataTransfer?.files[0]);
		}}
	>
		<input
			bind:this={input}
			class="visually-hidden"
			type="file"
			accept={ACCEPT}
			onchange={(e) => choose(e.currentTarget.files?.[0])}
		/>
		{#if file}
			<strong>{file.name}</strong>
			<span>{(file.size / 1048576).toFixed(1)} MB. Choose a different file</span>
		{:else}
			<strong>Choose a song</strong>
			<span>or drop it here. MP3, WAV, M4A, OGG or FLAC, up to {MAX_MB} MB</span>
		{/if}
	</label>

	<details class="options">
		<summary>Options</summary>
		<div class="option-grid">
			<label class="field">
				How much of the song
				<select bind:value={seconds}>
					<option value={0}>The whole song</option>
					<option value={60}>The first minute</option>
					<option value={120}>The first two minutes</option>
				</select>
			</label>
			<label class="field">
				Key
				<select bind:value={doKey}>
					<option value="">Work it out for me</option>
					{#each NOTE_NAMES as name (name)}
						<option value={name}>do = {name}</option>
					{/each}
				</select>
			</label>
			<label class="check">
				<input type="checkbox" bind:checked={voiceOnly} />
				Only a voice, no instruments
			</label>
		</div>
	</details>

	<button class="button make" type="submit" disabled={!file || uploading}>
		{uploading ? 'Uploading…' : 'Make the solfa'}
	</button>
	{#if error}<p class="error" role="alert">{error}</p>{/if}
	<p class="hint">The song starts playing straight away. The solfa fills in as it is worked out.</p>
</form>

<style>
	.upload {
		display: grid;
		gap: var(--space-4);
		max-width: 34rem;
	}

	.drop {
		display: grid;
		gap: var(--space-1);
		padding: var(--space-6) var(--space-5);
		border: 2px dashed var(--rule);
		border-radius: var(--radius-panel);
		background: var(--surface);
		cursor: pointer;
	}

	.drop:hover,
	.drop.dragging {
		border-color: var(--indigo);
	}

	.drop:focus-within {
		outline: 3px solid var(--focus);
		outline-offset: 2px;
	}

	.drop.chosen {
		border-style: solid;
		border-color: var(--indigo);
	}

	.drop strong {
		font-family: var(--font-display);
		font-size: var(--step-1);
		overflow-wrap: anywhere;
	}

	.drop span {
		color: var(--slate);
		font-size: var(--step--1);
	}

	.options summary {
		cursor: pointer;
		color: var(--slate);
		font-weight: 600;
		width: max-content;
	}

	.option-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
		gap: var(--space-4);
		padding-top: var(--space-4);
	}

	.check {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		align-self: end;
		min-height: 44px;
	}

	.check input {
		width: 20px;
		height: 20px;
		accent-color: var(--indigo);
	}

	.make {
		justify-self: start;
		min-width: 14rem;
	}

	.error {
		color: var(--danger);
		margin: 0;
	}

	.hint {
		color: var(--slate);
		font-size: var(--step--1);
		margin: 0;
	}
</style>
