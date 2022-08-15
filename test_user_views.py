"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

# importing operating sstem- setting environ to testing db
import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


from app import app, CURR_USER_KEY

db.create_all()

# we do not want the CSRF in form. Hard to test
app.config['ETF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    '''Test user views for messages'''

    def setUp(self):
        '''Create test client and sample data.'''

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        user1= User.signUp("test1", "test1@gmail.com", "password", None)
        user2= User.signUp("test2", "test1@gmail.com", "password", None)

        test_user = User.singUp("test user", "test_user@aol.com", "password", None)

        user1.id = 88888
        user2.id = 99999
        test_user.id = 11111

        db.session.add_all([user1, user2, test_user])
        db.session.committ()

        self.user1 = user1
        self.user2 = user2

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()

    def test_users_index(self):
        '''Test all users in db.'''

        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))


    def test_users_search(self):
        '''Test get request searching for users.'''

        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))     

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.user1.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
 
    def test_add_like(self):
        m = Message(id=4040, text="testing add like", user_id=self.user1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.post("/messages/1984/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==4040).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)


    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="testing remove lieks").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.user1.id)

        l = Likes.query.filter(
            Likes.user_id==self.user1.id and Likes.message_id==m.id
        ).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            # deleting like
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)     


    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="testing auth like").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))
            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.user1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2, f3])
        db.session.commit()     


    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user.id

            resp = c.get(f"/users/{self.test_user.id}/followers")

            self.assertIn("user1", str(resp.data))
            self.assertNotIn("user2", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.test_user.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("user2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.test_user.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@user2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
