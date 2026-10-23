import { describe, expect, it } from 'vitest';
import fixture from './slides.fixture.json';
import { cleanSlides, layoutSheet, type Note } from './solfa';

describe('cleanSlides matches keyboard.clean_slides on real songs', () => {
	for (const [song, data] of Object.entries(fixture)) {
		it(`${song}, every possible do`, () => {
			data.cleaned_by_do.forEach((expected, doPc) => {
				expect(cleanSlides(data.notes as Note[], doPc, data.minor_by_do[doPc])).toEqual(expected);
			});
		});
	}
});

describe('layoutSheet', () => {
	const note = (start: number, end = start + 0.4): Note => ({ start, end, pitch_midi: 60 });

	it('starts a new line after a long gap and marks short rests', () => {
		const phrases = layoutSheet([note(0), note(0.5), note(1.2), note(3)], []);
		expect(phrases.map((p) => p.items.map((i) => i.kind))).toEqual([['note', 'note', 'rest', 'note'], ['note']]);
	});

	it('puts an intro chord on its own line and a chord change above the note it starts on', () => {
		const chords = [
			{ start: 0, end: 4, root: 9, quality: 'maj' as const },
			{ start: 4.9, end: 8, root: 2, quality: 'maj' as const }
		];
		const phrases = layoutSheet([note(4), note(5)], chords);
		expect(phrases[0].items).toEqual([{ kind: 'chord', chord: chords[0] }]);
		expect(phrases[1].items.map((i) => i.kind)).toEqual(['note', 'rest', 'note']);
		const second = phrases[1].items[2];
		expect(second.kind === 'note' && second.chordAbove).toEqual(chords[1]);
	});
});
