import random
import rotibot.storage as store
import typing as t

import hikari
import lightbulb

casino_plugin = lightbulb.Plugin("Casino", "Casino plugin for RotiBot")


@casino_plugin.command
@lightbulb.command("casino", "Casino commands for gambling addicts")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def casino_group(ctx: lightbulb.Context) -> None:
    pass


@casino_group.child
@lightbulb.option(
    "target", "The member's balance to be displayed.", hikari.User, required=False
)
@lightbulb.command("balance", "Display user's current balance")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def balance(ctx: lightbulb.Context) -> None:
    target = ctx.get_guild().get_member(ctx.options.target or ctx.user)

    if not target:
        await ctx.respond("That user is not in the server")
        return

    # Read in user data from CSV file
    users = store.read_csv()
    target_id = int(target.id)

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

    user = ctx.get_guild().get_member(ctx.user)
    user_id = int(user.id)

    users = store.read_csv()

    if user_id not in users.keys():
        await make_account(user, users)
        users = store.read_csv()

    user_bal = users[user_id]["balance"]

    bet_num = 0
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


@roll.set_error_handler
async def roll_error(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.errors.CommandIsOnCooldown):
        await event.context.respond(
            f"{event.context.author.mention}, roll command is on cooldown for {exception.retry_after:,.0f} seconds."
        )
    else:
        raise exception


"""
Function to create a new entry for a new user
"""


async def make_account(user: hikari.Member, users: t.Any):
    # Create new dictionary entry for the new user
    users[int(user.id)] = {"username": user.display_name, "balance": 10000}

    # Write updated dictionary to CSV file
    store.write_csv(users)


"""
Used to format numbers for better readability
"""


def formatBalance(balance):
    formattedBalance = "{:,}".format(balance)
    return formattedBalance


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(casino_plugin)
