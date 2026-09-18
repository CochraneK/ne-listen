import unittest
from nelisten.security import is_local_api

class SecurityTest(unittest.TestCase):
    def test_local_api_detection(self):
        self.assertTrue(is_local_api("http://127.0.0.1:3000"))
        self.assertTrue(is_local_api("http://localhost:3000"))
        self.assertFalse(is_local_api("https://example.com"))

if __name__ == "__main__":
    unittest.main()
