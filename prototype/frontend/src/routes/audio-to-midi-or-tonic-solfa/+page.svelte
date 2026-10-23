<script lang="ts">
	import Guide from '#lib/components/Guide.svelte';
</script>

<Guide
	title="Audio to MIDI, or tonic solfa?"
	path="/audio-to-midi-or-tonic-solfa"
	description="Audio to MIDI converters give you a file for music software. If you want to play or sing a song yourself, tonic solfa may be what you need. Here is the difference."
	lede="Audio to MIDI and audio to tonic solfa both find the notes in a recording. They give those notes to different people: MIDI to software, solfa to a musician."
>
	<h2>What a MIDI file is for</h2>
	<p>
		MIDI is a list of notes for music software and instruments to play back. You open it in a
		recording program, put a virtual instrument on it and edit it. It is the right choice if you
		produce music, arrange in a program like a digital audio workstation, or want to drive a keyboard
		or synthesiser from software.
	</p>
	<p>
		Opened on its own, a MIDI file is usually shown as a piano roll: bars on a grid. That is easy for
		software and hard to read while you play.
	</p>

	<h2>What tonic solfa is for</h2>
	<p>
		Tonic solfa is for a person to read and play. Each note is a syllable, do re mi fa so la ti, that
		says where the note sits in the key. If you learned music in a choir or a church, it may be the
		notation you already know.
	</p>

	<h2>Which one to choose</h2>
	<div class="table-scroll">
		<table>
			<thead>
				<tr><th scope="col">You want to</th><th scope="col">Choose</th></tr>
			</thead>
			<tbody>
				<tr><td>Learn to play or sing a song</td><td>Tonic solfa</td></tr>
				<tr><td>Teach a tune to a choir or a class</td><td>Tonic solfa</td></tr>
				<tr><td>Edit the notes in music software</td><td>MIDI</td></tr>
				<tr><td>Replace the sound with a different instrument</td><td>MIDI</td></tr>
			</tbody>
		</table>
	</div>
	<p>
		SolfaFlow makes tonic solfa. It does not export MIDI files yet. If you need MIDI, open-source tools
		such as Spotify's Basic Pitch convert audio to MIDI.
	</p>
</Guide>
