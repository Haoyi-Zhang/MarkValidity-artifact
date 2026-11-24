def parse_music(music_string: str) -> List[int]:
	notes = music_string.split()
	notes_map = {'o ': 4, 'o| ': 2, '.| ': 1}
	return [notes_map[note + ' '] for note in notes]
