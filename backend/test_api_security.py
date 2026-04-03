import os
import tempfile
import unittest

try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import database
    import main
    import webhook as webhook_utils
except ModuleNotFoundError:
    TestClient = None
    create_engine = None
    sessionmaker = None
    database = None
    main = None
    webhook_utils = None


@unittest.skipUnless(TestClient is not None, "FastAPI 测试依赖未安装")
class APISecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "attendance-test.db")
        cls.webhook_path = os.path.join(cls.temp_dir.name, "webhook-config.json")

        database.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False}
        )
        database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
        webhook_utils.WEBHOOK_CONFIG_FILE = cls.webhook_path

        database.Base.metadata.create_all(bind=database.engine)
        cls.client_cm = TestClient(main.app)
        cls.client = cls.client_cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)
        cls.temp_dir.cleanup()

    def setUp(self):
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)
        if os.path.exists(self.webhook_path):
            os.remove(self.webhook_path)
        main.startup()

    def login(self, name: str, password: str) -> str:
        response = self.client.post("/api/login", json={"name": name, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["token"]

    def admin_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.login('admin', 'admin123')}"}

    def create_member(self, name: str, password: str = "member123") -> int:
        response = self.client.post(
            "/api/users",
            json={"name": name, "password": password, "role": "member"},
            headers=self.admin_headers()
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["id"]

    def test_protected_lists_require_authentication(self):
        for endpoint in ["/api/shifts", "/api/time-off", "/api/overtime", "/api/shifts/team"]:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403, f"{endpoint}: {response.text}")

    def test_member_cannot_list_users_but_can_read_self(self):
        self.create_member("member_a")
        member_token = self.login("member_a", "member123")
        headers = {"Authorization": f"Bearer {member_token}"}

        users_response = self.client.get("/api/users", headers=headers)
        self.assertEqual(users_response.status_code, 403, users_response.text)

        me_response = self.client.get("/api/me", headers=headers)
        self.assertEqual(me_response.status_code, 200, me_response.text)
        self.assertEqual(me_response.json()["name"], "member_a")

    def test_member_cannot_query_other_members_records(self):
        member_a_id = self.create_member("member_a")
        member_b_id = self.create_member("member_b")
        member_token = self.login("member_a", "member123")
        headers = {"Authorization": f"Bearer {member_token}"}

        response = self.client.get(f"/api/time-off?user_id={member_b_id}", headers=headers)
        self.assertEqual(response.status_code, 403, response.text)

        own_response = self.client.get(f"/api/time-off?user_id={member_a_id}", headers=headers)
        self.assertEqual(own_response.status_code, 200, own_response.text)

    def test_backup_export_masks_sensitive_data_by_default(self):
        self.create_member("member_a")
        response = self.client.get("/api/backup/export", headers=self.admin_headers())
        self.assertEqual(response.status_code, 200, response.text)

        exported_users = response.json()["data"]["users"]
        self.assertTrue(all(user["password"] is None for user in exported_users))

        sensitive_response = self.client.get(
            "/api/backup/export?include_sensitive=true",
            headers=self.admin_headers()
        )
        self.assertEqual(sensitive_response.status_code, 200, sensitive_response.text)
        sensitive_users = sensitive_response.json()["data"]["users"]
        self.assertTrue(all(user["password"] for user in sensitive_users))

    def test_invalid_backup_import_returns_400_and_rolls_back(self):
        payload = {
            "users": [
                {"id": 1, "name": "admin", "password": "hashed", "role": "admin"}
            ],
            "shifts": [
                {"id": 1, "user_id": 999, "date": "2026-04-01", "shift_type": "早班"}
            ],
            "time_off_requests": [],
            "overtime_records": []
        }

        response = self.client.post("/api/backup/import", json=payload, headers=self.admin_headers())
        self.assertEqual(response.status_code, 400, response.text)

        with database.SessionLocal() as db:
            users = db.query(database.User).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].name, "admin")


if __name__ == "__main__":
    unittest.main()
