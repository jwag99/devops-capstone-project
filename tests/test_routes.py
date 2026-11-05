"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.common.error_handlers import internal_server_error
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    ######################################################################
    #  R E A D   T E S T   C A S E S
    ######################################################################

    def test_read_an_account(self):
        """ It should Read a single account """

        ## this creates acct and posts to DB
        account = self._create_accounts(1)[0]
        read_resp = self.client.get(
            f"{BASE_URL}/{account.id}",
            content_type="application/json"
        )

        self.assertEqual(read_resp.status_code, status.HTTP_200_OK)
        
        # Check the data is correct
        read_acct = read_resp.get_json()
        self.assertEqual(read_acct["name"], account.name)
        self.assertEqual(read_acct["email"], account.email)
        self.assertEqual(read_acct["address"], account.address)
        self.assertEqual(read_acct["phone_number"], account.phone_number)
        self.assertEqual(read_acct["date_joined"], str(account.date_joined))
    
    def test_read_an_account_not_found(self):
        """ It should read a single account and fail """

        read_resp = self.client.get(
            f"{BASE_URL}/{0}",
            content_type="application/json"
        )

        self.assertEqual(read_resp.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  L I S T   T E S T   C A S E S
    ######################################################################

    def test_list_accounts(self):
        """ It should list all accounts """

        read_resp = self.client.get(
            f"{BASE_URL}/list",
            content_type="application/json"
        )
        self.assertEqual(read_resp.status_code, status.HTTP_404_NOT_FOUND)

        ## this creates acct and posts to DB
        self._create_accounts(5)[0]

        read_resp = self.client.get(
            f"{BASE_URL}/list",
            content_type="application/json"
        )

        self.assertEqual(read_resp.status_code, status.HTTP_200_OK)
        
        # Check the data is correct
        read_accts = read_resp.get_json()
        self.assertEqual(len(read_accts),5)

    ######################################################################
    #  U P D A T E   T E S T   C A S E S
    ######################################################################

    def test_update_account_name(self):
        """ It should update an account """
        account = self._create_accounts(1)[0]
        old_name = account.name
        new_name = "New Name"
        account.name = "New Name"

        # happy case - update acct just created
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=account.serialize()
        )

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        updated_acct = response.get_json()
        self.assertEqual(updated_acct["id"],account.id)
        self.assertEqual(updated_acct["name"],new_name)
        self.assertEqual(updated_acct["email"],account.email)
        self.assertEqual(updated_acct["address"],account.address)
        self.assertEqual(updated_acct["phone_number"],account.phone_number)
        self.assertNotEqual(updated_acct["name"],old_name)

    # def test_update_account_email(self):
    #     """ It should update an account """
    #     account = self._create_accounts(1)[0]
    #     old_email = account.email
    #     new_email = "newexample@example.com"
    #     account.email = "newexample@example.com"

    #     # happy case - update acct just created
    #     # HTTP_200_OK
    #     response = self.client.put(
    #         f"{BASE_URL}/{account.id}",
    #         content_type="application/json"
    #     )

    #     self.assertEqual(response.status_code,status.HTTP_200_OK)
    #     updated_acct = response.get_json()
    #     self.assertEqual(updated_acct["name"],account.name)
    #     self.assertEqual(updated_acct["email"],new_email)
    #     self.assertEqual(updated_acct["address"],account.address)
    #     self.assertEqual(updated_acct["phone_number"],account.phone_number)
    #     self.assertNotEqual(updated_acct["name"],old_email)

    # def test_update_account_not_found(self):
    #     # sad case - update acct which does not exist
    #     # HTTP_404_NOT_FOUND

    #     response = self.client.put(
    #         f"{BASE_URL}/{0}",
    #         content_type="application/json"
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  E R R O R   T E S T   C A S E S
    ######################################################################

    def test_not_supported(self):
        """ It should fail with 405 Not Allowed """

        read_resp = self.client.post(
            f"{BASE_URL}/deleteAll",
            content_type="application/json"
        )

        self.assertEqual(read_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        read_resp = self.client.get(
            f"{BASE_URL}/deleteAll",
            content_type="application/json"
        )

        self.assertEqual(read_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_server_error(self):
        """It should handle an unexpected server error"""

        error = Exception("Unexpected database failure")

        with app.app_context():
            response, response_status = internal_server_error(error)

        self.assertEqual(
            response_status,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        data = response.get_json()
        self.assertEqual(
            data["status"],
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        self.assertEqual(data["error"], "Internal Server Error")
        self.assertEqual(data["message"], "Unexpected database failure")
