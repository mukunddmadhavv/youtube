import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import align_audio_tags as aat


class AlignAudioTagsTest(unittest.TestCase):
    def test_strip_audio_tags(self):
        self.assertEqual(
            aat.strip_audio_tags("[excited] Hello! [whispers] Secret."),
            "Hello! Secret.",
        )
        self.assertEqual(
            aat.strip_audio_tags("[pauses] Only words remain [calm]"),
            "Only words remain",
        )

    def test_parse_words_filters_tags_and_adjusts_tempo(self):
        text = "[excited] Hello world! [pauses] Good day."
        chars = list(text)
        starts = [i * 0.1 for i in range(len(chars))]
        ends = [(i + 1) * 0.1 for i in range(len(chars))]
        alignment = {
            "characters": chars,
            "character_start_times_seconds": starts,
            "character_end_times_seconds": ends,
        }
        words = aat.parse_words_from_alignment(alignment, tempo=2.0)
        self.assertEqual([w["word"] for w in words], ["Hello", "world!", "Good", "day."])
        # Check start time of first word is scaled by tempo (orig 1.0s / 2.0 = 0.5s)
        self.assertAlmostEqual(words[0]["start"], 0.5, places=2)

    def test_generate_srt_cues(self):
        words = [
            {"word": "How", "start": 0.0, "end": 0.4},
            {"word": "queues", "start": 0.4, "end": 0.9},
            {"word": "work", "start": 0.9, "end": 1.3},
        ]
        srt = aat.generate_srt_cues(words, max_words_per_cue=2)
        self.assertIn("00:00:00,000 --> 00:00:00,900", srt)
        self.assertIn("How queues", srt)
        self.assertIn("work", srt)


if __name__ == "__main__":
    unittest.main()
