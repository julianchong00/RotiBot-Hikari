from asyncore import write
import csv
import typing as t

# Reads users.csv and returns a Dictionary
def read_csv() -> t.Dict[int, t.Dict]:
    users = dict()
    with open("users.csv", "r") as file:
        csv_dict = csv.DictReader(file)

        user_dict = dict()
        for row in csv_dict:
            user_dict["username"] = row["username"]
            user_dict["balance"] = int(row["balance"])
            users[row["discordID"]] = user_dict

    return users


# Write from Dictionary into users.csv
def write_csv(users: t.Dict[int, t.Dict]) -> None:
    with open("users.csv", "w") as file:
        field_names = ["discordID", "username", "balance"]
        writer = csv.DictWriter(file, fieldnames=field_names)

        writer.writeheader()
        for discordID in users.keys():
            user_dict = dict()
            user_dict["discordID"] = discordID
            user_dict["username"] = users[discordID]["username"]
            user_dict["balance"] = users[discordID]["balance"]
            writer.writerow(user_dict)
