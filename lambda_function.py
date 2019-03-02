from __future__ import print_function
import boto3
import json
from botocore.vendored import requests
from decimal import Decimal


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('AlexaSessionData')

help_greeting = """ 
    <speak>   
        <emphasis level="strong"> Hello.</emphasis>
        <p> I'm Laio. </p>
        <p> You can ask me questions about laio machines in your area. </p>
        <p> What would you like to know about? </p>     
    </speak>"""

reprompt_text = "<speak> Anything else I can do for you </speak>"
MISSING_LYO_MESSAGE ="<speak><p> Sorry </p> I can't find that laio machine </speak>"
        

##############################
# Builders
##############################


def build_ssml(body):
    ssml = {} 
    ssml['type'] = 'SSML'
    ssml['ssml'] = body
    return ssml


def build_PlainSpeech(body):
    speech = {}
    speech['type'] = 'PlainText'
    speech['text'] = body
    return speech


def build_response(message, session_attributes={}):
    response = {}
    response['version'] = '1.0'
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    return response


def build_SimpleCard(title, body):
    card = {}
    card['type'] = 'Simple'
    card['title'] = title
    card['content'] = body
    return card


##############################
# Responses
##############################


def conversation(title, body, session_attributes):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard(title, body)
    speechlet['shouldEndSession'] = False
    speechlet['reprompt'] = build_PlainSpeech(reprompt_text)
    return build_response(speechlet, session_attributes=session_attributes)


def statement(title, body):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard(title, body)
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)


def ssml(title, body):
    speechlet = {}
    speechlet['outputSpeech'] = build_ssml(body)
    speechlet['card'] = build_SimpleCard("", "")
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)


def ssml_continue_session(title, body, session_attributes):
    speechlet = {}
    speechlet['outputSpeech'] = build_ssml(body)
    speechlet['card'] = build_SimpleCard("", "")
    speechlet['shouldEndSession'] = False
    speechlet['reprompt'] = build_PlainSpeech(reprompt_text)

    return build_response(speechlet, session_attributes=session_attributes)


def continue_dialog():
    message = {}
    message['shouldEndSession'] = False
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(message)


##############################
# Required Intents
##############################


def cancel_intent():
    # don't use CancelIntent as title it causes code reference error during certification
    return statement("CancelIntent", "Goodbye")


def help_intent():
    # same here don't use CancelIntent
   return ssml("", help_greeting)


def stop_intent():
    # here also don't use StopIntent
    return statement("StopIntent", "Goodbye")


def invalid_intent(event, context):
    invalid_speech = """ 
    <speak>   
        <p> Sorry </p>     
        <p> I wasn't able to understand your request. </p> 
        <p> Try again </p> 
       
    </speak>"""

    return ssml_continue_session("", invalid_speech, GetSessionAttributes(event))

##############################
# On Launch
##############################


def on_launch(event, context):
    return ssml_continue_session("", help_greeting, GetSessionAttributes(event))


##############################
# Routing
##############################


def intent_router(event, context):
    intent = event['request']['intent']['name']

    # Custom Intents

    if intent == "lyodataintent":
        return lyodata_intent(event, context)

    elif intent == "CycleByEINIntent":
        return Cycle_By_EIN_Intent(event, context)

    elif intent == "StatusByEINIntent":
        return Status_By_EIN_Intent(event, context)

    elif intent == "PhaseByEINIntent":
        return Phase_By_EIN_Intent(event, context)

    elif intent == "RemainingTimeByEINIntent":
        return Remaining_Time_By_EIN_Intent(event, context)

    elif intent == "NextMaintenanceDateByEINIntent":
        return Next_Maintenance_Date_By_EIN_Intent(event, context)

    elif intent == "AlarmsByEINIntent":
        return Alarms_By_EIN_Intent(event, context)

    elif intent == "AlarmsByStatusIntent":
        return Alarms_By_Status_Intent(event, context)

    elif intent == "AlarmsByAreaIntent":
        return Alarms_By_Area_Intent(event, context)

    elif intent == "AlarmsIntent":
        return Alarms_Intent(event, context)

    elif intent == "LeakTestResultsByEINIntent":
        return Leak_Test_Results_By_EIN_Intent(event, context)

    elif intent == "LastLeakTestDateByEINIntent":
        return Last_Leak_Test_Date_By_EIN_Intent(event, context)

    elif intent == "SummaryByEINIntent":
        return Summary_By_EIN_Intent(event,context)

    # Required Intents
    elif intent == "AMAZON.CancelIntent":
        return cancel_intent()

    elif intent == "AMAZON.HelpIntent":
        return help_intent()

    elif intent == "AMAZON.StopIntent":
        return stop_intent()

    else:
        return invalid_intent(event, context)

    return


##############################
# Program Entry
##############################


def lambda_handler(event, context):

    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.bd304b90-xxxx-xxxx-86ae-1e4fd4772bab"):
    #     raise ValueError("Invalid Application ID")

    if event["session"]["new"]:
        on_session_started(
            {"requestId": event["request"]["requestId"]}, event["session"])
    if event['request']['type'] == "LaunchRequest":
        with open('data.json') as f:
            data = json.load(f)

        return on_launch(event, context)

    elif event['request']['type'] == "IntentRequest":
        return intent_router(event, context)
    else:
        ein = GetLastEIN()
        print(f"this is happening {ein}")
        if type(ein) == int:
            reprompt_text = f"Would you like to know anything else regarding laio {ein}"
            return conversation("", reprompt_text, GetSessionAttributes(event))
        else:
            reprompt_text = "Anything else I can do for you"
            return conversation("", reprompt_text, GetSessionAttributes(event))


def on_session_started(session_started_request, session):
    print("Starting new session.")


def on_session_ended(session_ended_request, session):
    print("Ending session.")

##############################
# Custom Intents
##############################

# def lyodata_intent(event, context):

#     if event['session']['new']:
#         event['session']['attributes'] = {}

#     session_attributes = event['session']['attributes']
#     ein = event['request']['intent']['slots']['EIN']['value']
#     res = get_lyo_data_id(ein)
#     session_attributes['EIN'] = res['EIN']
#     session_attributes['EQUIPMENT_ID'] = res['EQUIPMENT_ID']

#     return conversation("lyodata_intent", "I've saved your lyo data to the session",
#                         session_attributes)


def lyodata_intent(event, context):

    dialog_state = event['request']['dialogState']

    if dialog_state in ("STARTED", "IN_PROGRESS"):
        return continue_dialog()

    elif dialog_state == "COMPLETED":
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        SaveSessionToDB(event, res)

        speech_text = """ 
        <speak>   
        <emphasis level="strong"> All done.</emphasis>
        <p> Your data has been loaded and cached </p>
        <p> What would you like to know about? </p>     
        </speak>"""
        return ssml_continue_session("lyodata_intent", speech_text, GetSessionAttributes(event))

    else:
        return statement("Cycle_By_EIN_Intent", "No dialog")


def Cycle_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Cycle_By_EIN_Intent",
                            f"The latest cycle is {res['CYCLE']} ", GetSessionAttributes(event))

    else:
        data = GetSessionDataByName(event, 'CYCLE')
        return conversation("Cycle_By_EIN_Intent",
                            f"The latest cycle is {data}", GetSessionAttributes(event))


def Status_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Status_By_EIN_Intent",
                            f"The latest status is {res['STATUS_VALUE']}", GetSessionAttributes(event))
    else:
        data = GetSessionDataByName(event, 'STATUS_VALUE')
        return conversation("Status_By_EIN_Intent",
                            f"The latest status is {data}", GetSessionAttributes(event))


def Phase_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Phase_By_EIN_Intent",
                            f"The latest phase is {res['PHASE']}", GetSessionAttributes(event))
    else:
        data = GetSessionDataByName(event, 'PHASE')
        return conversation("Phase_By_EIN_Intent",
                            f"The latest phase is {data}", GetSessionAttributes(event))


def Remaining_Time_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Remaining_Time_By_EIN_Intent",
                            f"The remaining time is {res['REMAINING_TIME']}", GetSessionAttributes(event))
    else:

        data = GetSessionDataByName(event, 'REMAINING_TIME')
        return conversation("Remaining_Time_By_EIN_Intent",
                            f"The remaining time is {data}", GetSessionAttributes(event))


def Next_Maintenance_Date_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))
        
        return conversation("Next_Maintenance_Date_By_EIN_Intent",
                            f"The next maintenance date is {res['NEXT_MAINTENANCE_DATE']}", GetSessionAttributes(event))
    else:

        data = GetSessionDataByName(event, 'NEXT_MAINTENANCE_DATE')
        return conversation("Next_Maintenance_Date_By_EIN_Intent",
                            f"The next maintenance date is {data}", GetSessionAttributes(event))


def Alarms_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))
        
        alarm_res = Building_Alarm_Helper(res)

        if alarm_res != "":
            speech_text = f"<speak> {alarm_res} </speak> "
            return ssml_continue_session("Alarms_By_EIN_Intent", speech_text, GetSessionAttributes(event))
        else:

             return conversation("Alarms_By_EIN_Intent",
                                 f"There are no current alarms for that laio", GetSessionAttributes(event))


def Building_Alarm_Helper (res):

    if res == "": 
        return ""

    alarms = res['ALARMS']
    alarm_res = ""
    alarm_arr = []
    if len(alarms) > 0:

        alarm_res += f"<p>There are multiple alarms going off.</p>" if len(
            alarms) > 1 else "<p>There's only one alarm going off </p>"
        for index, alarm in enumerate(alarms):
            alarm_res += f" <p> Alarm {index+1}. </p> <p> {alarm['ALARM_NAME']} </p> with status. {alarm['ALARM_STATUS']} "
            alarm_arr.append(alarm_res)

    return alarm_res


def Alarms_By_Status_Intent(event, context):

    value_dict = event['request']['intent']['slots']['status']
    status = value_dict.get("value")

    # try:
    #     if value_dict['resolutions']['resolutionsPerAuthority'][0]['status']['code'] == "ER_SUCCESS_NO_MATCH" :
    #         return continue_dialog()
    # except KeyError:
    #     pass

    data = get_lyo_data()
    alarm_res = ""
    count = 0
    for obj in data:
        if status != None:
            alarms = obj['ALARMS']
            for alarm in alarms:
                if alarm['ALARM_STATUS'].lower() == status:
                    count += 1
                    alarm_res += f" <p> Alarm {count}. </p> <p> {alarm['ALARM_NAME']} </p> <p> On Laio {obj['EIN']} </p>"

    if len(alarm_res) == 0:
        alarm_res = f"<p>Don't worry</p> <p> There are no {status} alarms </p>"
    else:
        alarm_res = ''.join(
            (f'<p> There is at least one {status} alarm currently </p>', alarm_res))

    speech_text = f"<speak> {alarm_res} </speak> "
    return ssml_continue_session("Alarms_By_Status_Intent", speech_text, GetSessionAttributes(event))


def Alarms_By_Area_Intent(event, context):
    value_dict = event['request']['intent']['slots']['Area']
    area_number = value_dict.get("value")

    data = get_lyo_data()
    alarm_res = ""
    count = 0

    for obj in data:

        if area_number != None and int(area_number) == obj['AREA']:
            alarms = obj['ALARMS']
            for alarm in alarms:
                count += 1
                alarm_res += f"<p> Alarm {count}. </p> <p> {alarm['ALARM_NAME']} </p> <p> On Laio {obj['EIN']} </p>"

    if len(alarm_res) == 0:
        alarm_res = f"<p>Don't worry</p> <p> There are no current alarms for that area </p>"
    elif count == 1:
        alarm_res = ''.join(
            (f'<p> There is one alarm currently in area {area_number} </p>', alarm_res))

    else:
        alarm_res = ''.join(
            (f'<p> There are {count} alarms currently in area {area_number} </p>', alarm_res))

    speech_text = f"<speak> {alarm_res} </speak> "
    return ssml_continue_session("", speech_text, GetSessionAttributes(event))


def Alarms_Intent(event, context):

    data = get_lyo_data()
    alarm_res = ""
    count = 0

    for obj in data:

            alarms = obj['ALARMS']
            for alarm in alarms:
                count += 1
                alarm_res += f"<p> Alarm {count}. </p> <p> {alarm['ALARM_NAME']} </p> <p> on Laio {obj['EIN']} in area {obj['AREA']} </p>"

    if len(alarm_res) == 0:
        alarm_res = f"<p>Don't worry</p> <p> There are no current alarms </p>"
    elif count == 1:
        alarm_res = ''.join(
            (f'<p> There is one alarm currently </p>', alarm_res))

    else:
        alarm_res = ''.join(
            (f'<p> There are {count} alarms currently </p>', alarm_res))

    speech_text = f"<speak> {alarm_res} </speak> "
    return ssml_continue_session("Alarms_Intent", speech_text, GetSessionAttributes(event))


def Leak_Test_Results_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Leak_Test_Results_By_EIN_Intent",
                            f"The results of the last leak test is {res['LEAK_TEST_RESULTS']}", GetSessionAttributes(event))
    else:
        data = GetSessionDataByName(event, 'LEAK_TEST_RESULTS')
        return conversation("Leak_Test_Results_By_EIN_Intent",
                            f"The latest leak test result is {data}", GetSessionAttributes(event))


def Last_Leak_Test_Date_By_EIN_Intent(event, context):
    value_dict = event['request']['intent']['slots']['EIN']

    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        return conversation("Last_Leak_Test_Date_By_EIN_Intent",
                            f"The date of the last leak test was {res['LEAK_TEST_START']}", GetSessionAttributes(event))
    else:
        data = GetSessionDataByName(event, 'LEAK_TEST_START')
        return conversation("Last_Leak_Test_Date_By_EIN_Intent",
                            f"The date of the last leak test was {data}", GetSessionAttributes(event))


def Summary_By_EIN_Intent (event, context):
    value_dict = event['request']['intent']['slots']['EIN']
    if value_dict.get("value") != None:
        ein = event['request']['intent']['slots']['EIN']['value']
        res = get_lyo_data_id(ein)

        if res == "":
            return ssml_continue_session("", MISSING_LYO_MESSAGE, GetSessionAttributes(event))

        alarm_info  = Building_Alarm_Helper(res)
        


        speech_text = f""" <speak> {alarm_info}
        <p>The current cycle is running {res['CYCLE']} and the remaining 
        time on the cycle is approximately {res['REMAINING_TIME']}</p>
        <p>The phase is {res['PHASE']} and status is {res['STATUS_VALUE']} </p>
        <p>The last leak test results were {res['LEAK_TEST_RESULTS']} and the 
        next maintenance date is {res['NEXT_MAINTENANCE_DATE']} </p>
            </speak>
        """


        return ssml_continue_session("Summary_By_EIN_Intent",
                            speech_text, GetSessionAttributes(event))
   


##############################
# Helper Methods
##############################

def GetLastEIN():
    response = table.get_item(Key={'name': 'Current'})
    return  response['Item']['EIN']

def GetSessionFromDB(event):
    response = table.get_item(Key={'name': 'Current'})
    print(response['Item']['CYCLE'])
    return statement("Greeting", response['Item']['CYCLE'])


def SaveSessionToDB(event, res):
    user_id = event['session']['user']['userId']
    intent = event["request"]['intent']['name']
    time = event["request"]['timestamp']
    table.delete_item(Key={'name': 'Current'})
    table.put_item(Item={
        'name': 'Current',
        'intent': intent,
        'user_id': user_id,
        'time': time,
        'EQUIPMENT_ID': res['EQUIPMENT_ID'],
        'EQUIPMENT_CLASS': res['EQUIPMENT_CLASS'],
        'STATUS_VALUE': res['STATUS_VALUE'],
        'UNIT_PROCEDURE_ID': res['UNIT_PROCEDURE_ID'],
        'LAST_CHANGED_DATE': res['LAST_CHANGED_DATE'],
        #        'MAINTENANCE_VALUE'     : Decimal(str(res['MAINTENANCE_VALUE']))      ,
        'EIN': res['EIN'],
        'CYCLE': res['CYCLE'],
        'PHASE': res['PHASE'],
        'START_TIME': res['START_TIME'],
        'ELAPSED_TIME': res['ELAPSED_TIME'],
        'END_TIME': res['END_TIME'],
        'AVERAGE_TIME': Decimal(str(res['AVERAGE_TIME'])),
        'REMAINING_TIME': str(res['REMAINING_TIME']),
        'NEXT_MAINTENANCE_DATE': res['NEXT_MAINTENANCE_DATE'],
        'LEAK_TEST_RESULTS': res['LEAK_TEST_RESULTS'],
        'LEAK_TEST_START': res['LEAK_TEST_START'],
    })

    return


def GetSessionDataByName(event, name):
    response = table.get_item(Key={'name': 'Current'})
    res = response['Item']

    if name == 'EIN':
        return res['EIN']
    elif name == 'CYCLE':
        return res['CYCLE']
    elif name == 'UNIT_PROCEDURE_ID':
        return res['UNIT_PROCEDURE_ID']
    elif name == 'STATUS_VALUE':
        return res['STATUS_VALUE']
    elif name == 'EQUIPMENT_ID':
        return res['EQUIPMENT_ID']
    elif name == 'EQUIPMENT_CLASS':
        return res['EQUIPMENT_CLASS']
    elif name == 'PHASE':
        return res['PHASE']
    elif name == 'START_TIME':
        return res['START_TIME']
    elif name == 'AVERAGE_TIME':
        return res['AVERAGE_TIME']
    elif name == 'REMAINING_TIME':
        return res['REMAINING_TIME']
    elif name == 'NEXT_MAINTENANCE_DATE':
        return res['NEXT_MAINTENANCE_DATE']
    elif name == 'LEAK_TEST_RESULTS':
        return res['LEAK_TEST_RESULTS']
    elif name == 'LEAK_TEST_START':
        return res['LEAK_TEST_START']
    else:
        return "I don't have a value for that"


def GetSessionAttributes(event):
    if event['session']['new']:
        event['session']['attributes'] = {}

    if event['session'].get('attributes') == None:
        event['session']['attributes'] = {}

    session_attributes = event['session']['attributes']
    return session_attributes


def get_lyo_data():

    try: 
        with open('data.json') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return None


def get_lyo_data_id(ein):

    try: 

        search_ein = int(ein)
        res = ""
        with open('data.json') as f:
            data = json.load(f)

        for obj in data:
            if obj["EIN"] == search_ein:
                res = obj

        return res
    except Exception as e:
        return None
        
