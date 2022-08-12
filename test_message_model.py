import os
from unittest import TestCase

from models import db, User, Message, Likes
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserMessageModelTestCase(TestCase):
    """Test views for Users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        user_one = User.signup("testuser", "testu@gmail.com", "password", None)

        user_one.id = 99999

        db.session.add(user_one)

        db.session.commit()

        self.user1 = user_one

        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message(self):
        """Message model"""

        message = Message(
            text="A message about stuff and other stuff",
            user_id = self.user1.id
        )

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user1.messages), 1)
        self.assertEqual(self.user1.messages[0].text, "A message about stuff and other stuff")

    def test_liking_messages(self):
        """Test that liking messages works"""

        message = Message(
            text="A message about stuff and other stuff",
            user_id = self.user1.id
        )

        message_dos = Message(
            text="A message about way cooler stuff than the last message posted by this user",
            user_id = self.user1.id
        )

        other_user = User.signup("another_user", "another_user@aol.com", "password", None)

        db.session.add(message)
        db.session.add(message_dos)
        db.session.add(other_user)

        other_user.likes.append(message_dos)

        db.session.commit()

        find_like = Likes.query.filter(Likes.user_id == other_user.id).all()
        self.assertEqual(len(find_like), 1)
        self.assertEqual(find_like[0].message_id, message_dos.id)