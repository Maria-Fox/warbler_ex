"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup("testuser", "testu@gmail.com", "password", None)
        user2 = User.signup("testuser2", "testu@yahoo.com", "password", None)
       
        user1.id = 998
        user2.id = 999

        db.session.add_all([user1, user2])
        db.session.commit()

        self.client = app.test_client()


    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="first@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


# Follwoing Tests

    def test_following_followers(self):
        """Test following and followers"""
    
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user2.followers), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    def test_is_following(self):
        '''Test is following'''

        self.user1.following.append(self.user2)
        db.session.commmit()

        self.assertFalse(self.user2.is_followed_by(self.user1))
        self.assertTrue(self.user1.is_followed_by(self.user2))

    def is_followed_by(self):
        '''Test followed by'''

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))


# Creating User

    def test_signup(self):
        '''Test creating new user/signing up.'''

        user_test = User.signup("testing_1", "test@email.com", "password1", None)

        user_id = 1111
        user_test.id = user_id

        db.session.commit()

        user_test = User.query.get_or_404(user_id)
        self.assertIsNotNone(user_test)
        self.assertIsInstance(user_test, User, msg="Is instance of User class")
        self.assertEqual(user_test.username, "testing_1")
        self.assertEqual(user_test.email, "test@email.com")

    def test_invalid_username_signup(self):
        '''Test invalid username/ fail'''

        invalid_username = User.signup(None, "test@aol.com", "password", None)
        uid = 456789
        invalid_username.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_email = User.signup("test456", None, "password", None)
        uid = 456789
        invalid_email.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("first_test", "email@aol.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("second_test", "email@aol.com", None, None)


# Testing Authentication

    def test_authentication(self):
        '''Test authentication a user'''
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1.id)
    
    def test_invalid_username(self):
        '''Should fail username'''
        self.assertFalse(User.authenticate("fail_username", "password"))

    def test_wrong_password(self):
        '''Should fail password'''
        self.assertFalse(User.authenticate(self.user1.username, "fail_password"))