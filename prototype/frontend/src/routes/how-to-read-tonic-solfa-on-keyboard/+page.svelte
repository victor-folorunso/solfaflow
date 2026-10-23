<script lang="ts">
	import Guide from '#lib/components/Guide.svelte';
	import { NOTE_NAMES } from '#lib/solfa.ts';

	const MAJOR = [0, 2, 4, 5, 7, 9, 11];
	const SYLLABLES = ['do', 're', 'mi', 'fa', 'so', 'la', 'ti'];
	// Keys with flats are named by their black key as SolfaFlow shows it (A#), with the flat name too.
	const FLAT_NAMES: Record<string, string> = { 'A#': 'B♭', 'D#': 'E♭', 'G#': 'A♭', 'C#': 'D♭', 'F#': 'G♭' };
	const name = (pc: number) => {
		const sharp = NOTE_NAMES[pc % 12];
		return FLAT_NAMES[sharp] ? `${FLAT_NAMES[sharp]} (${sharp})` : sharp;
	};
	const KEYS = ['C', 'G', 'D', 'A', 'F', 'A#'].map((k) => {
		const doPc = NOTE_NAMES.indexOf(k);
		return { key: name(doPc), notes: MAJOR.map((step) => name(doPc + step)) };
	});
</script>

<Guide
	title="How to read tonic solfa on the keyboard"
	path="/how-to-read-tonic-solfa-on-keyboard"
	description="Learn to play tonic solfa on the keyboard: find do in any key, read octave marks and sharps, and practise a song line by line."
	lede="Tonic solfa tells you how the notes of a tune relate to its home note, not which keys to press. Once you know where do is, every other syllable falls into place."
>
	<h2>Do is the home note, and it moves</h2>
	<p>
		In tonic solfa the scale is always do, re, mi, fa, so, la, ti, and do is the home note of the song.
		That home note can be any key. When a song is "in G", do is G. When it is in D, do is D. This is
		called movable do, and it is why the same solfa fits a song in any key.
	</p>
	<p>
		Written tonic solfa often shortens the syllables to letters: d r m f s l t. Older books spell them
		doh, ray, me, fah, soh, lah, te. They all mean the same seven notes.
	</p>

	<h2>Where each syllable falls in common keys</h2>
	<p>Find your key on the left; the row shows which key to press for each syllable.</p>
	<div class="table-scroll">
		<table>
			<thead>
				<tr>
					<th scope="col">do =</th>
					{#each SYLLABLES as syl (syl)}<th scope="col" class="solfa">{syl}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each KEYS as row (row.key)}
					<tr>
						<th scope="row">{row.key}</th>
						{#each row.notes as note, i (i)}<td>{note}</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<p>
		In C every syllable is a white key, which is why many players learn a song in C first. In
		SolfaFlow, "Moved so do = C" shows any song's key names as if it were in C.
	</p>

	<h2>High and low notes</h2>
	<p>
		The same syllable can be played in different octaves. A mark after the syllable moves it: an
		apostrophe for higher, a comma for lower. So <span class="solfa">do'</span> is the do above the
		usual one, and <span class="solfa">so,</span> is the so below it. SolfaFlow also writes the exact
		key, such as G3 or G4, under every syllable.
	</p>

	<h2>Sharps, flats and minor songs</h2>
	<ul>
		<li>
			A note between two scale notes gets a changed vowel. Raised notes end in -i: di, ri, fi, si, li.
			Fi is the black key just above fa.
		</li>
		<li>
			In minor songs the home note is la, not do. A song in A minor is written with do = C and centres
			on la. The raised so, si, is common in minor tunes.
		</li>
	</ul>

	<h2>Note lengths</h2>
	<p>
		Printed tonic solfa marks beats with colons and bar lines, and a dash means hold the note. SolfaFlow
		shows each note's length as a short bar under the syllable and lights the syllable while it sounds,
		so you can follow the timing by ear.
	</p>

	<h2>A way to practise a new song</h2>
	<ol>
		<li>Find do. Play do, re, mi, fa, so, la, ti, do' in the song's key until it feels natural.</li>
		<li>Listen to one line of the song while following the syllables.</li>
		<li>Play that line slowly. In SolfaFlow, set the speed to half.</li>
		<li>Play along with the recording at normal speed, then move to the next line.</li>
	</ol>
</Guide>
