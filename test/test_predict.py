import json
import os
import time
import unittest
from unittest.mock import patch
from src.run_filter import predict_label, get_issues, get_comments
# from test.data.test_data import get_comments


# Load environment variables
TOKEN = os.getenv('REPO_ACCESS_TOKEN')
KEY = os.getenv('API_KEY')

OWNER = "virtual-labs"
REPO = "bugs-virtual-labs"

# API URL and headers
url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
headers = {
    "Authorization": f"token {TOKEN}"
}

def loadIssuesFromLocal(filename='./test/data/issues.json'):
    with open(filename, "r") as file:
        issuesJson = json.load(file)
    return issuesJson


class TestPredictLabel(unittest.TestCase):

    def setUp(self):
        super().setUp()
        with open('test/data/issueComments.json', 'r') as file:
            self.comments = json.load(file)
    
    def tearDown(self):
        return super().tearDown()

    def test_predict_label(self):

        for idx, comment in enumerate(self.comments):
            for _, value in comment.items():
                predict_label(value)
            if idx % 14 == 13:
                time.sleep(70)



@unittest.skip("Will implement later")
class TestFetchGithubData(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_github_data(self, mock_get):
        # Mock the JSON response to return a fake JSON data
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            'id': 123456,
            'name': 'example-repo',
            'owner': {'login': 'example-user'}
        }
        mock_response.status_code = 200  # Simulate a successful response

        # Call the function you're testing
        url = "https://api.github.com/repos/example-user/example-repo"
        result = fetch_github_data(url)

        # Assert that the mock was called correctly
        mock_get.assert_called_once_with(url)

        # Assert the returned data is as expected
        self.assertEqual(result, {
            'id': 123456,
            'name': 'example-repo',
            'owner': {'login': 'example-user'}
        })


@unittest.skip("Only needed for initial data setup")
class TestGetIssues(unittest.TestCase):
    
    def setUp(self):
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_fetch_github_data(self):

        issues = get_issues(url, headers)
        with open("issues.json", "w") as file:
            json.dump(issues, file)

@unittest.skip("Only needed for initial data setup")
class TestGetComments(unittest.TestCase):
    def setUp(self):
        super().setUp()

        with open("test/data/issues.json", "r") as file:
            self.issuesJSON = json.load(file)

    
    def tearDown(self):
        return super().tearDown()
    
    def testGetComments(self):
        comments = get_comments(self.issuesJSON)
        with open('test/data/issueComments.json', 'w') as file:
            json.dump(comments, file, indent=2)

if __name__ == '__main__':
    unittest.main()
