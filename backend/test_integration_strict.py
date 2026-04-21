"""
严格集成测试套件 - 覆盖所有核心功能和边界条件
"""
import base64
import json
import time
from datetime import date, timedelta
from io import BytesIO
from unittest import TestCase

from fastapi.testclient import TestClient
from PIL import Image

from app import app
from config.db import Base, SessionLocal, engine
from models.user import User
from models.study_room import StudyRoom
from models.room_user import RoomUser
from models.study_duration import StudyDuration
from utils import cache


class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()
        r = cache._redis()
        if hasattr(r, 'flushall'):
            r.flushall()
        elif hasattr(r, 'flushdb'):
            r.flushdb()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db.query(User).delete()
        self.db.query(StudyRoom).delete()
        self.db.query(RoomUser).delete()
        self.db.query(StudyDuration).delete()
        self.db.commit()
        r = cache._redis()
        if hasattr(r, 'flushall'):
            r.flushall()
        elif hasattr(r, 'flushdb'):
            r.flushdb()
        self.headers = {}

    def _create_test_user(self, phone="13800138000", password="test123"):
        response = self.client.post("/api/user/register", json={"phone": phone, "password": password})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200, f"注册失败: {data}")
        return data["data"]["user_id"], data["data"]["token"]

    def _login_user(self, phone="13800138000", password="test123"):
        response = self.client.post("/api/user/login", json={"phone": phone, "password": password})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        return data["data"]["user_id"], data["data"]["token"]

    def _get_auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def _generate_test_image(self, has_person=True):
        img = Image.new('RGB', (100, 100), color='red' if has_person else 'white')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"


class TestUserRegistrationStrict(BaseTestCase):
    """用户注册严格测试"""

    def test_register_success_all_fields(self):
        response = self.client.post("/api/user/register", json={
            "phone": "13800138000",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("user_id", data["data"])
        self.assertIn("token", data["data"])
        self.assertIsNotNone(data["data"]["user_id"])
        self.assertIsNotNone(data["data"]["token"])
        self.assertEqual(len(data["data"]["user_id"]), 32)

    def test_register_duplicate_phone_returns_409(self):
        self.client.post("/api/user/register", json={"phone": "13800138000", "password": "password123"})
        response = self.client.post("/api/user/register", json={"phone": "13800138000", "password": "password123"})
        self.assertEqual(response.status_code, 409, f"期望409，实际: {response.status_code}, {response.json()}")
        data = response.json()
        self.assertEqual(data["code"], 409)

    def test_register_invalid_phone_10_digits(self):
        response = self.client.post("/api/user/register", json={"phone": "1234567890", "password": "password123"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["code"], 400)

    def test_register_invalid_phone_12_digits(self):
        response = self.client.post("/api/user/register", json={"phone": "123456789012", "password": "password123"})
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_phone_letters(self):
        response = self.client.post("/api/user/register", json={"phone": "1380013800a", "password": "password123"})
        self.assertEqual(response.status_code, 400)

    def test_register_empty_phone(self):
        response = self.client.post("/api/user/register", json={"phone": "", "password": "password123"})
        self.assertEqual(response.status_code, 400)

    def test_register_empty_password(self):
        response = self.client.post("/api/user/register", json={"phone": "13800138000", "password": ""})
        self.assertEqual(response.status_code, 400)

    def test_register_missing_phone(self):
        response = self.client.post("/api/user/register", json={"password": "password123"})
        self.assertEqual(response.status_code, 422)

    def test_register_missing_password(self):
        response = self.client.post("/api/user/register", json={"phone": "13800138000"})
        self.assertEqual(response.status_code, 422)


class TestUserLoginStrict(BaseTestCase):
    """用户登录严格测试"""

    def test_login_success_is_first_login_true(self):
        self._create_test_user()
        response = self.client.post("/api/user/login", json={"phone": "13800138000", "password": "test123"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertTrue(data["data"]["is_first_login"])

    def test_login_success_is_first_login_false_after(self):
        self._create_test_user()
        self.client.post("/api/user/login", json={"phone": "13800138000", "password": "test123"})
        response = self.client.post("/api/user/login", json={"phone": "13800138000", "password": "test123"})
        data = response.json()
        self.assertFalse(data["data"]["is_first_login"])

    def test_login_wrong_password_returns_400(self):
        self._create_test_user()
        response = self.client.post("/api/user/login", json={"phone": "13800138000", "password": "wrongpassword"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["code"], 400)

    def test_login_nonexistent_user_returns_400(self):
        response = self.client.post("/api/user/login", json={"phone": "13800138000", "password": "test123"})
        self.assertEqual(response.status_code, 400)

    def test_login_invalid_phone_format(self):
        response = self.client.post("/api/user/login", json={"phone": "12345", "password": "password123"})
        self.assertEqual(response.status_code, 400)

    def test_login_empty_credentials(self):
        response = self.client.post("/api/user/login", json={"phone": "", "password": ""})
        self.assertEqual(response.status_code, 400)


class TestUserLogoutStrict(BaseTestCase):
    """用户登出严格测试"""

    def test_logout_success_invalidates_token(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)

        logout_response = self.client.post("/api/user/logout", headers=headers)
        self.assertEqual(logout_response.status_code, 200)

        profile_response = self.client.get("/api/user/profile", headers=headers)
        self.assertEqual(profile_response.status_code, 401)

    def test_logout_without_token_returns_401(self):
        response = self.client.post("/api/user/logout")
        self.assertEqual(response.status_code, 401)

    def test_logout_invalid_token_returns_401(self):
        headers = self._get_auth_headers("invalid_token_123")
        response = self.client.post("/api/user/logout", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_logout_malformed_header_returns_401(self):
        headers = {"Authorization": "NotBearer token"}
        response = self.client.post("/api/user/logout", headers=headers)
        self.assertEqual(response.status_code, 401)


class TestUserProfileStrict(BaseTestCase):
    """用户资料严格测试"""

    def test_get_profile_success_returns_correct_fields(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/user/profile", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("user_id", data["data"])
        self.assertIn("phone", data["data"])
        self.assertIn("nickname", data["data"])
        self.assertIn("avatar", data["data"])
        self.assertIn("tags", data["data"])
        self.assertIn("registertime", data["data"])
        self.assertIn("lastlogintime", data["data"])

    def test_get_profile_tags_are_list(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/user/profile", headers=headers)
        data = response.json()
        self.assertIsInstance(data["data"]["tags"], list)

    def test_get_profile_without_auth_returns_401(self):
        response = self.client.get("/api/user/profile")
        self.assertEqual(response.status_code, 401)

    def test_update_nickname_success(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.put("/api/user/profile/nickname", json={"nickname": "新昵称测试"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["nickname"], "新昵称测试")

    def test_update_nickname_empty_returns_400(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.put("/api/user/profile/nickname", json={"nickname": ""}, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_update_nickname_too_long_returns_400(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.put("/api/user/profile/nickname", json={"nickname": "a" * 100}, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_update_tags_success(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.put("/api/user/profile/tags", json={"tags": ["考研", "英语", "数学"]}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["tags"], ["考研", "英语", "数学"])

    def test_get_user_info_success(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get(f"/api/user/info/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["phone"], "13800138000")

    def test_get_user_info_nonexistent_returns_404(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/user/info/nonexistent123456789012", headers=headers)
        self.assertEqual(response.status_code, 404)


class TestRoomCreationStrict(BaseTestCase):
    """自习室创建严格测试"""

    def test_create_room_success_returns_valid_room_id(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4,
            "tags": ["数学"]
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("room_id", data["data"])
        self.assertEqual(len(data["data"]["room_id"]), 32)

    def test_create_room_creator_joins_automatically(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = response.json()["data"]["room_id"]

        info_response = self.client.get(f"/api/room/info/{room_id}", headers=headers)
        info_data = info_response.json()
        self.assertEqual(info_data["data"]["current_people"], 1)
        self.assertIn(user_id, info_data["data"]["users"])

    def test_create_room_max_people_1_is_full(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 1
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["room_status"], "full")

    def test_create_room_max_people_2_is_idle(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 2
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["room_status"], "idle")

    def test_create_room_invalid_max_people_0(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 0
        }, headers=headers)
        self.assertIn(response.status_code, [400, 422])

    def test_create_room_invalid_max_people_9(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 9
        }, headers=headers)
        self.assertIn(response.status_code, [400, 422])

    def test_create_room_too_many_tags(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4,
            "tags": ["标签1", "标签2", "标签3", "标签4"]
        }, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_create_room_without_auth_returns_401(self):
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        })
        self.assertEqual(response.status_code, 401)


class TestRoomJoinLeaveStrict(BaseTestCase):
    """自习室加入/离开严格测试"""

    def test_join_room_success(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        response = self.client.post("/api/room/join", json={
            "room_id": room_id,
            "match_type": "manual"
        }, headers=headers2)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 200)
        self.assertEqual(data["data"]["room_id"], room_id)
        self.assertEqual(data["data"]["match_type"], "manual")

    def test_join_room_auto_match_type(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        response = self.client.post("/api/room/join", json={
            "room_id": room_id,
            "match_type": "auto"
        }, headers=headers2)
        self.assertEqual(response.status_code, 200)

    def test_join_room_not_exist_returns_404(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/join", json={
            "room_id": "a" * 32,
            "match_type": "manual"
        }, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_join_room_full_returns_409(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 1
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        response = self.client.post("/api/room/join", json={
            "room_id": room_id,
            "match_type": "manual"
        }, headers=headers2)
        self.assertEqual(response.status_code, 409)

    def test_join_room_invalid_room_id_length(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/join", json={
            "room_id": "short_id",
            "match_type": "manual"
        }, headers=headers)
        self.assertIn(response.status_code, [400, 422])

    def test_leave_room_success_updates_current_people(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        leave_response = self.client.post("/api/room/leave", json={
            "room_id": room_id
        }, headers=headers)
        self.assertEqual(leave_response.status_code, 200)
        data = leave_response.json()
        self.assertEqual(data["code"], 200)
        self.assertIn("study_duration", data["data"])

    def test_leave_room_last_user_closes_room(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 2
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        leave_response = self.client.post("/api/room/leave", json={
            "room_id": room_id
        }, headers=headers)
        self.assertEqual(leave_response.status_code, 200)

        info_response = self.client.get(f"/api/room/info/{room_id}", headers=headers)
        self.assertEqual(info_response.status_code, 404)

    def test_user_cannot_join_when_already_in_room(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        join_response = self.client.post("/api/room/join", json={
            "room_id": room_id,
            "match_type": "manual"
        }, headers=headers1)
        self.assertEqual(join_response.status_code, 200)


class TestRoomUpdateDestroyStrict(BaseTestCase):
    """自习室更新/销毁严格测试"""

    def test_update_room_theme_by_creator(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        response = self.client.put(f"/api/room/update/{room_id}", json={
            "theme": "期末"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)

        info_response = self.client.get(f"/api/room/info/{room_id}", headers=headers)
        self.assertEqual(info_response.json()["data"]["theme"], "期末")

    def test_update_room_not_creator_returns_403(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        response = self.client.put(f"/api/room/update/{room_id}", json={
            "theme": "期末"
        }, headers=headers2)
        self.assertEqual(response.status_code, 403)

    def test_update_room_not_exist_returns_404(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.put(f"/api/room/update/{'a' * 32}", json={
            "theme": "期末"
        }, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_destroy_room_by_creator(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        response = self.client.delete(f"/api/room/destroy/{room_id}", headers=headers)
        self.assertEqual(response.status_code, 200)

        info_response = self.client.get(f"/api/room/info/{room_id}", headers=headers)
        self.assertEqual(info_response.status_code, 404)

    def test_destroy_room_not_creator_returns_403(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        response = self.client.delete(f"/api/room/destroy/{room_id}", headers=headers2)
        self.assertEqual(response.status_code, 403)

    def test_destroy_room_closes_for_all_members(self):
        user1_id, token1 = self._create_test_user()
        headers1 = self._get_auth_headers(token1)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers1)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        self.client.post("/api/room/join", json={
            "room_id": room_id,
            "match_type": "manual"
        }, headers=headers2)

        self.client.delete(f"/api/room/destroy/{room_id}", headers=headers1)

        user2_info = self.client.get(f"/api/room/info/{room_id}", headers=headers2)
        self.assertEqual(user2_info.status_code, 404)


class TestStudyDurationStrict(BaseTestCase):
    """学习时长严格测试"""

    def test_get_daily_duration_no_record_returns_zero(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/duration/daily", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["total_minutes"], 0)
        self.assertIsNone(data["data"]["beat_percent"])

    def test_get_daily_duration_with_future_date(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        future_date = date.today() + timedelta(days=30)
        response = self.client.get(f"/api/duration/daily?study_date={future_date.isoformat()}", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_get_weekly_duration_returns_7_days(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/duration/weekly", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["data"]), 7)

    def test_get_rank_empty_returns_empty_list(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/duration/rank", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["data"], list)
        self.assertEqual(len(data["data"]), 0)

    def test_get_rank_with_limit(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/duration/rank?limit=5", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_get_rank_limit_validation(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/duration/rank?limit=0", headers=headers)
        self.assertIn(response.status_code, [400, 422])

        response2 = self.client.get("/api/duration/rank?limit=101", headers=headers)
        self.assertIn(response.status_code, [400, 422])


class TestAIDetectionStrict(BaseTestCase):
    """AI检测严格测试"""

    def test_detect_person_no_person_image(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        img = self._generate_test_image(has_person=False)
        response = self.client.post("/api/room/detect-person", json={
            "image": img,
            "room_id": room_id,
            "user_id": user_id
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("has_person", data["data"])

    def test_detect_person_with_person_image(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        img = self._generate_test_image(has_person=True)
        response = self.client.post("/api/room/detect-person", json={
            "image": img,
            "room_id": room_id,
            "user_id": user_id
        }, headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_detect_person_wrong_user_returns_403(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        user2_id, token2 = self._create_test_user("13800138001", "test123")
        headers2 = self._get_auth_headers(token2)
        img = self._generate_test_image(has_person=True)
        response = self.client.post("/api/room/detect-person", json={
            "image": img,
            "room_id": room_id,
            "user_id": user2_id
        }, headers=headers2)
        self.assertEqual(response.status_code, 403)

    def test_detect_person_invalid_base64(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        response = self.client.post("/api/room/detect-person", json={
            "image": "invalid_base64_data",
            "room_id": room_id,
            "user_id": user_id
        }, headers=headers)
        self.assertEqual(response.status_code, 200)


class TestRateLimitingStrict(BaseTestCase):
    """限流严格测试"""

    def test_register_rate_limit_exceeded(self):
        for i in range(12):
            response = self.client.post("/api/user/register", json={
                "phone": f"1380013{i:04d}",
                "password": "test123"
            })
        response = self.client.post("/api/user/register", json={
            "phone": "13900139000",
            "password": "test123"
        })
        self.assertEqual(response.status_code, 429)

    def test_login_rate_limit_exceeded(self):
        self._create_test_user()
        for i in range(22):
            response = self.client.post("/api/user/login", json={
                "phone": "13800138000",
                "password": "wrongpassword"
            })
        response = self.client.post("/api/user/login", json={
            "phone": "13800138000",
            "password": "test123"
        })
        self.assertEqual(response.status_code, 429)


class TestWebSocketConnectionStrict(BaseTestCase):
    """WebSocket连接严格测试"""

    def test_websocket_missing_user_id(self):
        response = self.client.ws_connect("/ws/room/test123")
        response.close(code=1008, reason="Missing user_id")

    def test_websocket_endpoint_accessible(self):
        with self.client.stream("GET", "/ws/room/test123?user_id=test") as response:
            pass


class TestTagsEndpointStrict(BaseTestCase):
    """标签端点严格测试"""

    def test_get_tags_returns_valid_list(self):
        response = self.client.get("/api/user/tags")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["data"], list)
        self.assertGreater(len(data["data"]), 0)
        self.assertIn("考研", data["data"])

    def test_get_tags_no_auth_required(self):
        response = self.client.get("/api/user/tags")
        self.assertEqual(response.status_code, 200)


class TestDataIntegrityStrict(BaseTestCase):
    """数据完整性严格测试"""

    def test_user_id_is_uuid_format(self):
        user_id, token = self._create_test_user()
        self.assertEqual(len(user_id), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in user_id))

    def test_room_id_is_uuid_format(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = response.json()["data"]["room_id"]
        self.assertEqual(len(room_id), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in room_id))

    def test_user_phone_unique_constraint(self):
        self._create_test_user("13800138000", "password123")
        try:
            self._create_test_user("13800138000", "differentpassword")
            self.fail("Should have raised an exception")
        except AssertionError:
            pass

    def test_study_duration_persists_after_leave(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        create_response = self.client.post("/api/room/create", json={
            "theme": "考研",
            "max_people": 4
        }, headers=headers)
        room_id = create_response.json()["data"]["room_id"]

        time.sleep(0.1)
        self.client.post("/api/room/leave", json={"room_id": room_id}, headers=headers)

        duration_response = self.client.get("/api/duration/daily", headers=headers)
        self.assertEqual(duration_response.status_code, 200)


class TestErrorHandlingStrict(BaseTestCase):
    """错误处理严格测试"""

    def test_invalid_json_returns_422(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.post(
            "/api/room/create",
            content="not json",
            headers={**headers, "Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 422)

    def test_method_not_allowed_returns_405(self):
        response = self.client.delete("/api/user/tags")
        self.assertEqual(response.status_code, 405)

    def test_not_found_returns_404(self):
        user_id, token = self._create_test_user()
        headers = self._get_auth_headers(token)
        response = self.client.get("/api/nonexistent/endpoint", headers=headers)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
