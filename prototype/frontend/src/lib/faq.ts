// Shown on the home page and published as FAQPage structured data, so the two never disagree.
export const FAQ = [
	{
		q: 'Is SolfaFlow free?',
		a: 'Yes. Upload a song and get the tonic solfa at no cost.'
	},
	{
		q: 'Which songs work best?',
		a: 'Songs with one clear lead singer. SolfaFlow writes the tune the lead voice sings, with the chords underneath. Choir harmonies and backing vocals are not written out, and sections with no singing, such as a keyboard intro, show chords only.'
	},
	{
		q: 'How accurate is it?',
		a: 'It is automatic, so expect some wrong notes, most often where the singer slides, ornaments or sings very fast. Check it by ear. If the key sounds wrong, change do and every syllable updates at once.'
	},
	{
		q: 'What does "do = G" mean?',
		a: 'Tonic solfa is movable: do is the home note of the song, and it can be any key. "do = G" means play do on G, re on A, mi on B and so on. SolfaFlow writes the key under every syllable so you never have to work it out.'
	},
	{
		q: 'Why are some syllables underlined?',
		a: 'Singers often slide into a note, which can sound like a sharp or flat. SolfaFlow writes the note the singer was aiming for and underlines it. Choose "Exact" in the player to see what was actually sung.'
	},
	{
		q: 'Is my song shared with anyone?',
		a: 'No. Your song is only used to make your solfa. It is not added to any public library.'
	}
] as const;
