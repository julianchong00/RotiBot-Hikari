import random
import typing as t

import hikari
import lightbulb
from lightbulb.ext import tasks

import rotibot.storage as store
import rotibot.database as db

casino_plugin = lightbulb.Plugin("Casino", "Casino plugin for RotiBot")

"""
Defining casino command group
"""


@casino_plugin.command
@lightbulb.command("casino", "Casino commands for gambling addicts")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def casino_group(ctx: lightbulb.Context) -> None:
    pass


"""
Balance command: !balance @user
"""


@casino_group.child
@lightbulb.option(
    "target", "The member's balance to be displayed.", hikari.User, required=False
)
@lightbulb.command("balance", "Display user's current balance")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def balance(ctx: lightbulb.Context) -> None:
    target = ctx.get_guild().get_member(ctx.options.target or ctx.user)
    target_id = int(target.id)

    if not target:
        await ctx.respond("That user is not in the server")
        return

    # Check if target ID is in database, if not, make a new user and print default balance value
    users = await create_new_user_account(target)

    # Retrieve balance from users dict
    target_balance = users[target_id]["balance"]
    await ctx.respond(
        f"{target.mention}, you currently have {formatBalance(target_balance)} points."
    )


"""
Roll command: !roll @bet
"""


@casino_group.child
@lightbulb.option("bet", "The amount of points to bet", str, required=True)
@lightbulb.add_cooldown(180, 1, lightbulb.buckets.UserBucket)
@lightbulb.command(
    "roll",
    "Rolls a dice between 1 and 100. If higher than 50, return 1.5x the bet. Otherwise, lose bet.",
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def roll(ctx: lightbulb.Context) -> None:
    bet = ctx.options.bet
    bet_num = 0

    user = ctx.get_guild().get_member(ctx.user)
    user_id = int(user.id)

    users = await create_new_user_account(user)

    user_bal = users[user_id]["balance"]

    if bet == "all":
        if user_bal > 1000000:
            bet_num = 1000000
        elif user_bal > 0:
            bet_num = user_bal
        else:
            await ctx.respond(
                f"{user.mention}, you do not have enough points to bet that amount."
            )
            return
    elif bet.isnumeric():
        bet_num = int(bet)
        if bet_num > user_bal:
            await ctx.respond(
                f"{user.mention}, you do not have enough points to bet that amount."
            )
            return
    else:
        await ctx.respond("Invalid bet parameter.")

    random.seed()
    roll = random.randrange(101)

    if roll == 100:
        users[user_id]["balance"] += bet_num * 3
        await ctx.respond(
            f"{user.mention}, you rolled {str(roll)} and have earned {formatBalance(bet_num * 3)} points. Roll is now on cooldown for 3 minutes."
        )
    elif roll < 51:
        users[user_id]["balance"] -= bet_num
        await ctx.respond(
            f"{user.mention}, you rolled {str(roll)} and have lost {formatBalance(bet_num)} points. Roll is now on cooldown for 3 minutes."
        )
    else:
        users[user_id]["balance"] += int(bet_num * 1.5)
        await ctx.respond(
            f"{user.mention}, you rolled {str(roll)} and have earned {formatBalance(int(bet_num * 1.5))} points. Roll is now on cooldown for 3 minutes."
        )

    store.write_csv(users)


"""
Error handling function for roll command
"""


@roll.set_error_handler
async def roll_error(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.CommandIsOnCooldown):
        await event.context.respond(
            f"{event.context.author.mention}, roll command is on cooldown for {exception.retry_after:,.0f} seconds."
        )
    elif isinstance(exception, lightbulb.CommandInvocationError):
        await event.context.respond(
            f"{event.context.author.mention}, something went wrong during invocation of command {event.context.command.name}."
        )
    else:
        raise exception


"""
Give command: !give @user @gift_amount
"""


@casino_group.child
@lightbulb.option(
    "user", "The user to give a specified amount of points", hikari.User, required=True
)
@lightbulb.option(
    "amount",
    "Amount to be gifted to specified user",
    int,
    required=True,
    min_value=1,
)
@lightbulb.command("give", "Gives a user a specified amount of points")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def give(ctx: lightbulb.Context) -> None:
    gift_amount = ctx.options.amount

    target = ctx.options.user
    target_id = int(target.id)

    user = ctx.get_guild().get_member(ctx.user)
    user_id = int(user.id)

    if not target:
        await ctx.respond("That user is not in the server.")
        return
    if gift_amount <= 0:
        await ctx.respond(f"{user.mention}, gift amount has to be greater than 0.")
        return
    if target_id == user_id:
        await ctx.respond(f"{user.mention}, you cannot give points to yourself.")
        return

    users = await create_new_user_account(user)
    users = await create_new_user_account(target)

    gifter_balance = users[user_id]["balance"]
    if gift_amount > gifter_balance:
        await ctx.respond(f"{user.mention}, you do not have enough points to gift.")
    else:
        users[user_id]["balance"] -= gift_amount
        users[target_id]["balance"] += gift_amount
        await ctx.respond(
            f"{target.mention}, {user.mention} has given you {formatBalance(gift_amount)} points."
        )
        store.write_csv(users)


"""
Error handling function for give command
"""


@give.set_error_handler
async def give_error(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.CommandInvocationError):
        await event.context.respond(
            f"{event.context.author.mention}, something went wrong during invocation of command {event.context.command.name}."
        )
    else:
        raise exception


"""
Top command: !top
"""


@casino_group.child
@lightbulb.option(
    "number_of_users",
    "Number of users to be displayed on leaderboard",
    int,
    required=False,
    min_value=1,
    default=5,
)
@lightbulb.command("top", "Shows leaderboard of top users with the most points.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def top(ctx: lightbulb.Context) -> None:
    num_users = ctx.options.number_of_users

    user = ctx.get_guild().get_member(ctx.author)

    users = await create_new_user_account(user)

    # Sort users dictionary in reverse order by point balance
    sorted_users = sorted(
        users.items(), key=lambda item: item[1]["balance"], reverse=True
    )

    # Get top num_users users from sorted list
    top_users = []

    if len(users) > num_users:
        for i in range(num_users):
            user_points = (
                sorted_users[i][1]["username"],
                formatBalance(sorted_users[i][1]["balance"]),
            )
            top_users.append(user_points)
    else:
        for i in range(len(users)):
            user_points = (
                sorted_users[i][1]["username"],
                formatBalance(sorted_users[i][1]["balance"]),
            )
            top_users.append(user_points)

    # Prepare embed to send as message
    embed_desc = f"Top {len(top_users)} Users"
    embed = hikari.Embed(
        title="Points Leaderboard", description=embed_desc, color=user.accent_colour
    )
    for index in range(len(top_users)):
        embed.add_field(
            name=str(index + 1) + ". " + top_users[index][0],
            value=top_users[index][1],
            inline=True,
        )
    await ctx.respond(embed=embed)


"""
ADMIN Donate command: !donate @user @amount
"""


@casino_group.child
@lightbulb.add_checks(
    lightbulb.checks.has_role_permissions(hikari.Permissions.ADMINISTRATOR)
)
@lightbulb.option("user", "User to donate points to", hikari.Member, required=True)
@lightbulb.option(
    "amount", "Amount of points to be donated", int, required=True, min_value=1
)
@lightbulb.command("donate", "Admin command for donating points to a user")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def donate(ctx: lightbulb.Context) -> None:
    donation_amount = ctx.options.amount

    target = ctx.options.user
    target_id = int(target.id)

    if not target:
        await ctx.respond("That user is not in the server.")
        return

    # Makes an account for the mentioned user if user doesn't have an account
    users = await create_new_user_account(target)

    users[target_id]["balance"] += donation_amount
    await ctx.respond(
        f"{target.mention}, {formatBalance(donation_amount)} point(s) have been added to your balance."
    )
    store.write_csv(users)


@donate.set_error_handler
async def donate_error(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            f"{event.context.author.mention}, you do not have the required permissions to run {event.context.command.name} command."
        )
    elif isinstance(exception, lightbulb.CommandInvocationError):
        await event.context.respond(
            f"{event.context.author.mention}, something went wrong during invocation of command {event.context.command.name}."
        )
    else:
        raise exception


"""
Function to check whether a user is in CSV file and create new account if not
"""


async def create_new_user_account(user: hikari.Member) -> t.Dict[int, t.Dict]:
    users = store.read_csv()
    if int(user.id) not in users.keys():
        await make_account(user, users)
        users = store.read_csv()
    return users


"""
Function to create a new entry for a new user
"""


async def make_account(user: hikari.Member, users: t.Dict[int, t.Dict]) -> None:
    # Create new dictionary entry for the new user
    users[int(user.id)] = {"username": user.display_name, "balance": 10000}

    # Write updated dictionary to CSV file
    store.write_csv(users)


"""
Passive income for people with accounts in server. 250 points every 5 minutes.
"""


@tasks.task(m=5, auto_start=True)
async def passive_income() -> None:
    users = store.read_csv()

    for user in users.values():
        user["balance"] += 250

    store.write_csv(users)


"""
Save CSV data to PostgreSQL database every 10 minutes.
"""


@tasks.task(m=10, auto_start=True)
async def backup_data() -> None:
    users = store.read_csv()

    if len(users) > 0:
        db.saveAllUsers(users)


"""
Used to format numbers for better readability
"""


def formatBalance(balance):
    formattedBalance = "{:,}".format(balance)
    return formattedBalance


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(casino_plugin)
