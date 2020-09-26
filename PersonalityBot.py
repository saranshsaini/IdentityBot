import praw
from ibm_watson import PersonalityInsightsV3
from ibm_watson import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from PersonalityDictionaries import high_personality_dictionary, low_personality_dictionary, consumption_dictionary
from praw.exceptions import RedditAPIException
import time
IBM_key = '<YOUR KEY HERE>'
IBM_URL = '<YOUR IBM API ENDPOINT HERE>'

authenticator = IAMAuthenticator('{}'.format(IBM_key))
personality_insights = PersonalityInsightsV3(
    version='2017-10-13',
    authenticator=authenticator
)

personality_insights.set_service_url('{}'.format(IBM_URL))
personality_insights.set_default_headers({'x-watson-learning-opt-out': "true"})

reddit = praw.Reddit(client_id="<REDDIT BOT CLIENT ID>",
                     client_secret="<REDDIT BOT CLIENT SECRET>",
                     password='BOT ACCOUNT PASSWORD',
                     user_agent="<BOT VERSION>",
                     username="<BOT ACCOUNT USERNAME>")


def get_mentioned_user():
    for mention in reddit.inbox.mentions(limit=1):
        body = mention.body.split()[1]
        body = str(body)
        if body.startswith('u/') or body.startswith('/u/'):
            if True:#time.time()-mention.created_utc<60:
                mentioned_user = body.split('/')[1]
            elif time.time()-mention.created_utc>=60:
                print('Not a new mention, not in correct time frame')
                mentioned_user = None
            if mentioned_user == 'makerofapis':
                print('cant call me to analyze myself')
                mentioned_user = None

        else:
            mentioned_user = None
            print('not in proper u/ or /u/ format')

    return mentioned_user, mention


def get_user_comment_document(user):
    if user:
        comment_document = ''
        for comment in reddit.redditor("{}".format(user)).comments.new(limit=25):
            comment_document = comment_document + '. ' + comment.body
        return comment_document
    else:
        print('No user')
        return None


def access_personality_api(document):
    try:
        profile = personality_insights.profile(
            document,
            'application/json',
            content_type='text/plain',
            consumption_preferences=True,
            raw_scores=True
        ).get_result()
        return profile
    except ApiException as ex:
        print("Method failed with status code " + str(ex.code) + ": " + ex.message)

    return None


def get_facets(data):
    facetslist = {}
    facet_descriptions = ""
    for trait in data['personality']:
        for facet in trait['children']:
            facetslist[facet['trait_id']] = facet['percentile']
    sorted_facets = sorted(facetslist.items(), key=lambda x: x[1])
    greatest_facets = sorted_facets[-3:]
    lowest_facets = sorted_facets[:3]
    for facet in greatest_facets:
        facet_descriptions += high_personality_dictionary[facet[0]] + " "
    high_facet_descriptions = "You " + high_personality_dictionary[greatest_facets[0][0]] + ", " + \
                              high_personality_dictionary[greatest_facets[1][0]] + ", and " + \
                              high_personality_dictionary[greatest_facets[2][0]] + ". "
    low_facet_descriptions = "You " + low_personality_dictionary[lowest_facets[0][0]] + ", " + \
                             low_personality_dictionary[lowest_facets[1][0]] + ", and " + \
                             low_personality_dictionary[lowest_facets[2][0]] + "."
    return high_facet_descriptions + '\n' + low_facet_descriptions


def get_needs(data):
    needslist = {}
    needs = ""
    high_needs = ""
    low_needs = ""
    for need in data['needs']:
        needslist[need['name']] = need['percentile']
    sorted_facets = sorted(needslist.items(), key=lambda x: x[1])
    greatest_needs = sorted_facets[-3:]
    lowest_needs = sorted_facets[:3]
    high_needs += greatest_needs[0][0] + ", " + greatest_needs[1][0] + ", and " + greatest_needs[2][0]
    low_needs += lowest_needs[0][0] + ", " + lowest_needs[1][0] + ", and " + lowest_needs[2][0]
    needs += f"You value {high_needs} more than you might value {low_needs}."
    return needs


def consumption_preferences(data):
    yes_consumptions = []
    no_consumptions = []
    for pref in data["consumption_preferences"]:
        for preference in pref["consumption_preferences"]:
            if preference['score'] == 1 and preference["consumption_preference_id"] in consumption_dictionary:
                # print(consumption_dictionary[["consumption_preference_id"]])
                yes_consumptions.append(consumption_dictionary[preference["consumption_preference_id"]])
            if preference['score'] == 0 and preference["consumption_preference_id"] in consumption_dictionary:
                # print(consumption_dictionary[["consumption_preference_id"]])
                no_consumptions.append(consumption_dictionary[preference["consumption_preference_id"]])
    yes_consumptions_string = ', '.join(map(str, yes_consumptions))
    no_consumptions_string = ', '.join(map(str, no_consumptions))
    report = f'Here are some things I think you might like:\n\n {yes_consumptions_string}. \n\n \n\n Here are some ' \
             f'things I think you might not like as much:\n\n {no_consumptions_string}.'
    return report


def final_func():
    while True:
        mentioned_user, mention = get_mentioned_user()
        print(mentioned_user)
        if mentioned_user:
            comment_document = get_user_comment_document(mentioned_user)
            data = access_personality_api(comment_document)
            print('data:',data)
            if data:
                facets=get_facets(data)
                needs=get_needs(data)
                consumption=consumption_preferences(data)
                try:
                    mention.reply(
                        f"{facets} \n\n \n\n"
                        
                        f" {needs} \n\n \n\n"
                        
                        f" {consumption}"
                    )
                    print('I replied!')
                except RedditAPIException as exception:
                    print(exception)
                    pass
        #comment_document = get_user_comment_document(mentioned_user)
        #data = access_personality_api(comment_document)
        # if mentioned_user:
        #     try:
        #         mention.reply('hello')
        #     except RedditAPIException as exception:
        #         print(exception)
        print('sleeping...')
        time.sleep(60)
        #return  None#f"{get_facets(data)} \n {get_needs(data)} \n {consumption_preferences(data)}"


print(final_func())
