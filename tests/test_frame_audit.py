import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from frame_audit import sample_times

class SamplingTest(unittest.TestCase):
    def test_entire_timeline_and_last_frame(self):
        times = sample_times(319.933333, 30)
        self.assertEqual(times[:-1], [float(x) for x in range(0, 319, 3)])
        self.assertAlmostEqual(times[-1], 319.9, places=4)
    def test_exact_multiple_has_no_sample_past_end(self):
        self.assertEqual(sample_times(6,30)[:2], [0,3])
        self.assertLess(sample_times(6,30)[-1],6)
    def test_invalid_duration(self):
        for duration in (0,-1,float('nan')):
            with self.assertRaises(ValueError): sample_times(duration,30)

if __name__ == '__main__': unittest.main()
