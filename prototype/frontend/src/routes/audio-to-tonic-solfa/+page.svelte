<script lang="ts">
	import Guide from '#lib/components/Guide.svelte';
</script>

<Guide
	title="Audio to tonic solfa"
	path="/audio-to-tonic-solfa"
	description="Turn a song recording into tonic solfa automatically. How AI music transcription finds the tune, the key and the chords, and what to expect from it."
	lede="Most music transcription software turns audio into sheet music on a staff. SolfaFlow turns it into tonic solfa instead, the notation many singers and church keyboardists already read."
>
	<h2>What happens to your song</h2>
	<ol>
		<li>
			The singer is separated from the instruments, so the band does not get mistaken for the tune.
		</li>
		<li>
			An AI model trained on singing writes down each note the lead voice sings: when it starts, how
			long it lasts and its pitch.
		</li>
		<li>
			Each note is moved onto the nearest keyboard key. If the recording is slightly sharp or flat
			overall, or the singer drifts, that is corrected first.
		</li>
		<li>
			The key is worked out from the tune, and every note is written as a syllable relative to do.
		</li>
		<li>The chords are read from the instruments and written above the solfa where they change.</li>
	</ol>
	<p>
		The song starts playing as soon as it is uploaded, and the solfa fills in part by part while the
		rest is worked out.
	</p>

	<h2>Why tonic solfa and not sheet music</h2>
	<p>
		Audio to sheet music tools write notes on a staff, which assumes you read staff notation. Many
		singers and keyboard players learned tonic solfa instead, especially in church and school choirs
		across Nigeria, Ghana, South Africa and Kenya. Tonic solfa also shows how a note sits in the key,
		which is how you hear a tune, so a song is easier to learn by ear in solfa.
	</p>

	<h2>What works well, and what does not</h2>
	<ul>
		<li>Best: songs with one clear lead singer, recorded cleanly.</li>
		<li>
			Harder: fast runs, heavy vibrato and slides between notes. SolfaFlow cleans up slides, and you
			can switch to the exact version to see what was really sung.
		</li>
		<li>
			Not written out: choir harmony parts and backing vocals. Sections with no singing, like a
			keyboard intro, show their chords only.
		</li>
		<li>
			Short clips are harder to key correctly. If the key sounds wrong, change do in the player and
			every syllable updates.
		</li>
	</ul>
	<p>
		No automatic transcription is perfect. Treat the result as a strong first draft and check it by ear:
		the player can play the detected notes on a piano sound next to the original.
	</p>
</Guide>
