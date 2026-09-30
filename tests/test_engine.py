import unittest
import pandas as pd
import numpy as np
from src.engine import (
    haversine,
    _has_col,
    suggest_mapping,
    analyze_column,
    segment_into_trips,
)

class TestEngine(unittest.TestCase):
    def test_haversine_same_point(self):
        """Distance between the same coordinates should be zero."""
        dist = haversine(28.6139, 77.2090, 28.6139, 77.2090)
        self.assertAlmostEqual(dist, 0.0, places=4)

    def test_haversine_known_distance(self):
        """Distance for 1 degree longitude at equator is approximately 111.19 km."""
        dist = haversine(0.0, 0.0, 0.0, 1.0)
        self.assertTrue(110.0 < dist < 112.5)

    def test_has_col(self):
        """Verify _has_col correctly checks mapped features and dataframe columns."""
        df = pd.DataFrame({"latitude": [28.6], "longitude": [77.2]})
        mapped = {"latitude", "longitude"}

        self.assertTrue(_has_col(df, mapped, "latitude", "longitude"))
        self.assertFalse(_has_col(df, mapped, "latitude", "speed"))
        self.assertFalse(_has_col(df, {"latitude"}, "latitude", "longitude"))

    def test_suggest_mapping(self):
        """Verify column name heuristic suggestion for common telematics fields."""
        self.assertEqual(suggest_mapping("latitude"), "latitude")
        self.assertEqual(suggest_mapping("longitude"), "longitude")
        self.assertEqual(suggest_mapping("veh_spd"), "vehicle_speed")

    def test_analyze_column_numeric(self):
        """Verify summary statistics for numeric series."""
        s = pd.Series([10.0, 20.0, 30.0, np.nan, 50.0], name="test_speed")
        result = analyze_column("test_speed", s)

        self.assertEqual(result["name"], "test_speed")
        self.assertEqual(result["inferred_type"], "numeric")
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual(result["missing_pct"], 20.0)
        self.assertEqual(result["mean"], 27.5)

    def test_segment_into_trips_with_trip_id(self):
        """Verify segmentation when trip_id column is provided."""
        df = pd.DataFrame({
            "trip_id": ["T1", "T1", "T2", "T2"],
            "speed": [30, 45, 20, 60]
        })
        trips, summaries = segment_into_trips(df)
        self.assertEqual(len(trips), 2)
        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0]["trip_id"], "T1")
        self.assertEqual(summaries[1]["trip_id"], "T2")

if __name__ == "__main__":
    unittest.main()
