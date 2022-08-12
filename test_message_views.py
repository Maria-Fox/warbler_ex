"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.test_user = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.test_user.id = 9876
        self.t_user_id = self.test_user.id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = client.post("/messages/new", data={"text": "Attempt at posting1"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Attempt at posting1")

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Attempt at posting2"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
        
    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 999999

            resp = c.post("/messages/new", data={"text": "Attempt at posting3"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_show(self):

        new_message = Message(
            id=1234,
            text="tesing message",
            user_id=self.testuser_id
        )  
        
        db.session.add(new_message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                # message needs to be associated w a user
                sess[CURR_USER_KEY] = self.test_user.id
            
            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))

    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user.id
            
            resp = c.get('/messages/99999999')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):

        m = Message(
            id=4646,
            text="testing delete",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/4646/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(4646)
            self.assertIsNone(m)
    

    def test_unauthorized_message_delete(self):

        # Unauthorized user/ not signed in trying to delete the message
        u = User.signup(username="unauthorized_user",
                        email="not_permission@aol.com",
                        password="password",
                        image_url=None)
        u.id = 464646

        #Message is owned by test_user- user sending request not authorized to delete
        m = Message(
            id= 9876,
            text="a test message",
            user_id = self.t_user_id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 464646

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

    def test_message_delete_no_authentication(self):

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)   