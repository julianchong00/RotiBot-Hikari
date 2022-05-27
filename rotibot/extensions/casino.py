import json
import typing as t

import hikari
import lightbulb

casino_plugin = lightbulb.Plugin("Casino", "Casino plugin for RotiBot")


@casino_plugin.command
@lightbulb.option(
    "target", "The member's balance to be displayed.", hikari.User, required=False
)
@lightbulb.command("balance", "Display user's current balance")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.Context) -> None:
    target = ctx.get_guild().get_member(ctx.options.target or ctx.user)

    if not target:
        await ctx.respond("That user is not in the server")
        return

    users = await load_users()
    target_id = target.id

    # Check if target ID is in database, if not, make a new user and print default balance value
    if target_id not in users.keys():
        await make_account(target, users)
        await ctx.respond(f"{target.mention}, you currently have 10,000 points.")
    else:
        # Retrieve balance from users dict
        target_balance = users[target_id]["balance"]
        await ctx.respond(
            f"{target.mention}, you currently have {formatBalance(target_balance)} points."
        )


"""
Function to create a new entry for a new user
"""


async def make_account(user: hikari.Member, users: t.Any):
    # Create new dictionary entry for the new user
    users[user.id] = {"username": user.display_name, "balance": 10000}

    await save_users(users)


"""
Function to load user balances from json file
"""


async def load_users() -> t.Any:
    with open("users.json", "r") as f:
        users = json.load(f)
    return users


"""
Function to save user balances into json file
"""


async def save_users(users: t.Any) -> None:
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)


"""
Used to format numbers for better readability
"""


def formatBalance(balance):
    formattedBalance = "{:,}".format(balance)
    return formattedBalance


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(casino_plugin)
