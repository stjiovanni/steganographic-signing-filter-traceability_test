import os
import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import dashboard_api


class StressTestContractTests(unittest.TestCase):
    def test_invalid_condition_is_rejected_before_processing(self):
        client = TestClient(dashboard_api.app)
        response = client.post(
            "/api/stress_test",
            json={
                "image_id": "missing",
                "method": "trustmark",
                "transform_name": "jpeg_compression",
                "intensity": 7,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid intensity", response.json()["detail"])

    def test_response_contract_includes_verification_alias(self):
        fields = dashboard_api.StressTestRequest.model_fields
        self.assertEqual(
            set(fields), {"image_id", "method", "transform_name", "intensity", "payload"}
        )
        self.assertIsNone(fields["payload"].default)


if __name__ == "__main__":
    unittest.main()
