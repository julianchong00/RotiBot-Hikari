import os
import typing as t
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import storage as store

load_dotenv()
env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

DB_URI = os.getenv("DB_URI")

"""
PostgreSQL Database setup
"""
engine = create_engine(DB_URI)
base = declarative_base()


class User(base):
    __tablename__ = "User"
    discordID = Column(Integer, primary_key=True)
    username = Column(String)
    balance = Column(Integer)

    def __repr__(self):
        return "<User(discordID={}, username='{}', balance={})>".format(
            self.discordID, self.username, self.balance
        )


"""
Function to save all user data from CSV file into PostgreSQL database
"""


def saveAllUsers(users: t.Dict[int, t.Dict]) -> None:
    Session = sessionmaker(engine)
    session = Session()
    return


"""
Function to load all user data from PostgreSQL database into CSV file
"""


def loadAllUsers() -> None:
    Session = sessionmaker(engine)
    session = Session()

    users = session.query(User)

    outerDict = dict()
    for user in users:
        innerDict = dict()
        innerDict["username"] = user.username
        innerDict["balance"] = int(user.balance)
        outerDict[int(user.discordID)] = innerDict

    store.write_csv(outerDict)
