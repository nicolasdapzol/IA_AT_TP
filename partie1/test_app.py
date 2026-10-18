import unittest
from pathlib import Path

from app import app


ROOT = Path(__file__).resolve().parent


class FrameworkApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def load_example(self, index):
        path = ROOT / f"exemple_aba{index}.txt"
        return path.read_text(encoding="utf-8")

    def analyze(self, text, action):
        return self.client.post(
            "/api/analyze",
            json={"text": text, "action": action},
        )

    def test_home_and_healthcheck(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/healthz").json["status"], "ok")

    def test_five_examples_are_available(self):
        response = self.client.get("/api/examples")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 5)
        self.assertTrue(all(example["available"] for example in response.json))

    def test_each_example_supports_all_actions(self):
        for index in range(1, 6):
            text = self.load_example(index)
            for action in ("arguments", "properties", "noncircular", "atomic"):
                with self.subTest(example=index, action=action):
                    response = self.analyze(text, action)
                    self.assertEqual(response.status_code, 200, response.json)
                    self.assertEqual(response.json["action"], action)
                    self.assertIn("display", response.json["input_framework"])

    def test_cycle_conversion_removes_cycles_without_mutating_source(self):
        text = self.load_example(4)
        response = self.analyze(text, "noncircular")
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json["transformed"])
        self.assertFalse(response.json["properties"]["circular"])
        self.assertIn("r3", response.json["input_framework"]["source"])

    def test_atomic_conversion_produces_atomic_framework(self):
        response = self.analyze(self.load_example(1), "atomic")
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json["properties"]["atomic"])
        self.assertTrue(response.json["transformed"])

    def test_invalid_framework_and_unknown_action_are_rejected(self):
        invalid = self.client.post("/api/validate", json={"text": "pas un framework"})
        unknown = self.analyze(self.load_example(1), "unknown")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(unknown.status_code, 400)

    def test_private_url_is_rejected(self):
        response = self.client.post(
            "/api/import-url",
            json={"url": "http://127.0.0.1/framework.txt"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()