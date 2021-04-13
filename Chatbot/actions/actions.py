# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import re
import sqlite3
import uuid
import spacy

nlp = spacy.load('en_core_web_sm')

conn = sqlite3.connect('rasa_chatbot.db')

conn.execute('''CREATE TABLE IF NOT EXISTS INFO_ENTRY
         (ID INTEGER PRIMARY KEY     NOT NULL,
         UUID           CHAR    NOT NULL,
         NAME           TEXT    NOT NULL,
         PHONE            INT    NOT NULL,
         EMAIL        CHAR(50));''')
conn.close()

data_tuple = (str(uuid.uuid1()),)


class GetName(Action):

    def name(self) -> Text:
        return "ask_email"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.latest_message("text")
        line = nlp(name)
        for ent in list(line.ents):
            if ent.label_ == "PERSON":
                name = ent.text

        global data_tuple
        data_tuple += (name,)

        dispatcher.utter_message(text="Hi {}. Please type your email.".format(name))

        return []

class GetEmail(Action):

    def name(self) -> Text:
        return "ask_number"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        email = tracker.latest_message["text"]
        email = re.findall(r"([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)", email)
        global data_tuple
        data_tuple += (email[0],)

        dispatcher.utter_message(text="Please type your phone number")

        return []

class GetPhoneNumber(Action):

    def name(self) -> Text:
        return "save_number"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        phone_number = tracker.latest_message["text"]
        phone_number = re.findall(r"\+?\d[\d -]{8,12}\d", phone_number)
        global data_tuple
        data_tuple += (int(phone_number[0]),)

        dispatcher.utter_message(text="Do you want to save the details?(Yes/No)")

        return []

class SaveData(Action):
    def name(self) -> Text:
        return "say_goodbye"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        res = tracker.latest_message["text"]
        global data_tuple
        if res == "Yes" or res == "Y":
            try:
                conn = sqlite3.connect('rasa_chatbot.db')
                cursor = conn.cursor()
                print("Connected to SQLite")

                sqlite_insert_with_param = """INSERT INTO INFO_ENTRY
                                      (uuid, name, email, phone) 
                                      VALUES (?, ?, ?, ?);"""

                cursor.execute(sqlite_insert_with_param, data_tuple)
                conn.commit()

                cursor.close()

            except sqlite3.Error as error:
                print("Failed to insert Python variable into sqlite table", error, data_tuple)
            finally:
                if conn:
                    conn.close()
                    print("The SQLite connection is closed")
            dispatcher.utter_message(text="Thank you for sharing your details")
        else:
            dispatcher.utter_message(text="Good bye")




        return []
