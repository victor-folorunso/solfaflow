<script lang="ts">
	import Guide from '#lib/components/Guide.svelte';
</script>

<Guide
	title="Solfège and tonic solfa"
	path="/solfege-and-tonic-solfa"
	description="Solfège and tonic solfa both use do re mi, but not always in the same way. Fixed do, movable do, and which one SolfaFlow writes."
	lede="Both use do, re, mi. The difference is what do means: a fixed note, or the home note of whatever song you are playing."
>
	<h2>Fixed do</h2>
	<p>
		In fixed-do solfège, do is always C, re is always D, and so on, whatever key the song is in. The
		syllables are simply names for the notes. Fixed do is common in France, Italy, Spain and much of
		Latin America.
	</p>

	<h2>Movable do</h2>
	<p>
		In movable-do solfège, do is the home note of the song. In G, do is G; in F, do is F. A tune is
		written with the same syllables in any key, so the syllables tell you how each note feels in the
		key rather than its name.
	</p>

	<h2>Tonic solfa</h2>
	<p>
		Tonic solfa is a movable-do system developed in England in the 1800s by Sarah Glover and spread by
		John Curwen. It writes the syllables as letters (d r m f s l t), marks high and low notes with
		apostrophes and commas, and has its own way of writing rhythm with colons and bar lines. It became
		the standard notation for choirs and churches across much of Africa and in parts of Asia.
	</p>

	<h2>What SolfaFlow writes</h2>
	<ul>
		<li>Movable do: do is the home note of your song, and the player tells you which key it is.</li>
		<li>Minor songs are la-based: the home note of a minor song is la.</li>
		<li>Raised notes end in -i: di, ri, fi, si, li.</li>
		<li>The exact keyboard key under every syllable, so you are never left to work it out.</li>
	</ul>
	<p>
		If you read fixed do, use the key names under each syllable: they are the fixed note names.
	</p>
</Guide>
