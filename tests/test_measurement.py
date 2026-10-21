import math
import unittest
from fish_length.measurement import measure_endpoints


class MeasurementTests(unittest.TestCase):
    def measure(self, detections, grid=None, **kwargs):
        grid = grid if grid is not None else [[(0, 0, 1), None, (0.3, 0, 1)]]
        return measure_endpoints(detections, lambda x, y: grid[y][x], len(grid[0]),
                                 len(grid), unit=kwargs.pop("unit", "m"), **kwargs)

    def test_invalid_detection_does_not_shift_other_results(self):
        result = self.measure([[[0, 0], [1, 0]], [[0, 0], [2, 0]]])
        self.assertEqual([r.detection_index for r in result], [0, 1])
        self.assertEqual(result[0].status, "invalid_depth")
        self.assertIsNone(result[0].length_cm)
        self.assertAlmostEqual(result[1].length_cm, 30)

    def test_units_and_3d_distance(self):
        for unit, scale in (("m", 1), ("cm", 100), ("mm", 1000)):
            grid = [[(0, 0, scale), (0.03*scale, 0.04*scale, scale)]]
            result = self.measure([[[0, 0], [1, 0]]], grid, unit=unit)
            self.assertAlmostEqual(result[0].length_cm, 5)

    def test_invalid_depth(self):
        for point in (None, (0, 0, math.nan), (0, 0, math.inf), (0, 0, 0), (0, 0, -1)):
            result = self.measure([[[0, 0], [1, 0]]], [[(0, 0, 1), point]])
            self.assertEqual(result[0].status, "invalid_depth")

    def test_keypoints_and_bounds(self):
        examples = [([], "invalid_keypoints"), ([[0, 0]], "invalid_keypoints"),
                    ([[math.nan, 0], [2, 0]], "invalid_keypoints"),
                    ([[-0.1, 0], [2, 0]], "out_of_bounds"),
                    ([[0, 0], [3, 0]], "out_of_bounds"),
                    ([[0, 0, 0.1], [2, 0, 0.9]], "low_confidence"),
                    ([[0, 0], [0, 0]], "coincident_pixels")]
        for points, status in examples:
            with self.subTest(points=points):
                self.assertEqual(self.measure([points])[0].status, status)

    def test_empty(self):
        self.assertEqual(self.measure([]), [])

    def test_configuration_validation(self):
        for options in ({"unit": "feet"}, {"endpoint_indices": (0, 0)},
                        {"endpoint_indices": (-1, 1)}, {"min_confidence": 2}):
            with self.assertRaises(ValueError):
                self.measure([], **options)

    def test_endpoint_selection(self):
        result = self.measure([[[1, 0], [0, 0], [2, 0]]], endpoint_indices=(1, 2))
        self.assertAlmostEqual(result[0].length_cm, 30)


if __name__ == "__main__":
    unittest.main()
