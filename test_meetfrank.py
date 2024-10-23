import json
from bs4 import BeautifulSoup
from unittest import TestCase, TestLoader, TextTestRunner
from meetfrank import extract_from_offer, get_offer_htmls


class TestMeetFrank(TestCase):
    # checks whether two job offers are extracted and sorted properly
    def test_extract_from_offer(self):
        with open('test_html_code.json', 'r', encoding='UTF_8') as f:
            inputs_outputs = json.load(f)
        all_offers_dict, my_offers_dict = {}, {}
        for testcase in inputs_outputs:
            offer = BeautifulSoup(testcase['offer'], 'html.parser')
            extract_from_offer('https://meetfrank.com', offer, all_offers_dict, my_offers_dict)
            with self.subTest(testcase['test_name']):
                self.assertEqual(first=all_offers_dict,
                                 second=(testcase['all_offers_dict_result']),
                                 msg='Problem with all_offers_dict')
                self.assertEqual(first=my_offers_dict,
                                 second=(testcase['my_offers_dict_result']),
                                 msg='Problem with my_offers_dict')
            all_offers_dict.clear()
            my_offers_dict.clear()

    # checks whether a realistic amount of offers is scraped from an actual URL
    def test_get_soup_meetfrank(self):
        offers_html = get_offer_htmls('https://meetfrank.com/latest-remote-data-analytics-jobs-in-estonia')
        self.assertGreater(a=len(offers_html), b=2, msg='Problem finding offer elements from meetFrank')


if __name__ == '__main__':
    suite = TestLoader().loadTestsFromTestCase(TestMeetFrank)
    runner = TextTestRunner()
    runner.run(suite)
