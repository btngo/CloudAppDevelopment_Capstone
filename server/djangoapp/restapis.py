import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions


def get_request(url, **kwargs):
    #print(kwargs)
    #print("GET from {} ".format(url))
    api_key = kwargs.get("api_key")
    response = None
    try:
        # Call get method of requests library with URL and parameters
        if api_key:
            params = dict()
            params["text"] = kwargs["text"]
            params["version"] = kwargs["version"]
            params["features"] = kwargs["features"]
            params["return_analyzed_text"] = kwargs["return_analyzed_text"]
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
                                    auth=HTTPBasicAuth('apikey', api_key))
        else:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    #print("With status {} ".format(status_code))
    print("With resp {} ".format(response.text))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
def post_request(url, payload, **kwargs):
    print(kwargs)
    print("POST from {} ".format(url))
    print("POST payload {} ".format(payload))
    response = None
    try:
        # Call get method of requests library with URL and parameters
        response = requests.post(url, params=kwargs, json=payload)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    state = kwargs.get("state")
    if state:
        json_result = get_request(url, state=state)
    else:
        json_result = get_request(url)
    if json_result:
        # For each dealer object
        for dealer in json_result:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function

def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("dealerId")
    if id:
        json_result = get_request(url, dealerId=id)
    else:
        json_result = get_request(url)
    if json_result:
        reviews = json_result["data"]["docs"]
        for dealer_review in reviews:
            review_obj = DealerReview(dealership=dealer_review["dealership"],
                                   name=dealer_review["name"],
                                   purchase=dealer_review["purchase"],
                                   review=dealer_review["review"])
            if "id" in dealer_review:
                review_obj.id = dealer_review["id"]
            if "purchase_date" in dealer_review:
                review_obj.purchase_date = dealer_review["purchase_date"]
            if "car_make" in dealer_review:
                review_obj.car_make = dealer_review["car_make"]
            if "car_model" in dealer_review:
                review_obj.car_model = dealer_review["car_model"]
            if "car_year" in dealer_review:
                review_obj.car_year = dealer_review["car_year"]

            sentiment = analyze_review_sentiments(review_obj.review)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results


def get_dealer_by_id_from_cf(url, id):
    json_result = get_request(url, id=id)

    if json_result:
        dealers = json_result
        dealer_doc = dealers[0]
        car_dealer_obj = CarDealer(
            address=dealer_doc["address"], 
            city=dealer_doc["city"],
            id=dealer_doc["id"], 
            lat=dealer_doc["lat"], 
            long=dealer_doc["long"],
            full_name=dealer_doc["full_name"], 
            st=dealer_doc["st"], 
            zip=dealer_doc["zip"],
            short_name=dealer_doc["short_name"])
        return car_dealer_obj


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(dealer_review):
    API_KEY = "GbUvTBHbJ_yL__dZzFjTG9m_KnW9qll8cMSDmrzlmwzY"
    NLU_URL = 'https://api.eu-gb.natural-language-understanding.watson.cloud.ibm.com/instances/1c1c17b8-2f7e-441c-a159-ad302c84b14d'
    authenticator = IAMAuthenticator(API_KEY)
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2023-07-21', authenticator=authenticator)
    natural_language_understanding.set_service_url(NLU_URL)
    response = natural_language_understanding.analyze(
        text=dealer_review, 
        language='en',
        features=Features(
        sentiment=SentimentOptions(targets=[dealer_review]))).get_result()
    
    print("NLU resp {} ".format(response))
    label = json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']
    return(label)



