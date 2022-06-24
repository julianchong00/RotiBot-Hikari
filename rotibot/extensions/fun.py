import asyncio
import random

import hikari
import lightbulb
from lightbulb.ext.tungsten import tungsten

ANIMALS = {
    "Dog": "🐶",
    "Cat": "🐱",
    "Panda": "🐼",
    "Fox": "🦊",
    "Red Panda": "🐼",
    "Koala": "🐨",
    "Bird": "🐦",
    "Racoon": "🦝",
    "Kangaroo": "🦘",
}

fun_plugin = lightbulb.Plugin("Fun")


@fun_plugin.command
@lightbulb.command("fun", "All the entertainment commands you'll ever need")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def fun_group(ctx: lightbulb.Context) -> None:
    pass


"""
Meme command
"""


@fun_group.child
@lightbulb.command("meme", "Get a meme")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def meme_subcommand(ctx: lightbulb.Context) -> None:
    async with ctx.bot.d.aio_session.get(
        "https://meme-api.herokuapp.com/gimme"
    ) as response:
        res = await response.json()

        if response.ok and res["nsfw"] != True:
            link = res["postLink"]
            title = res["title"]
            img_url = res["url"]

            embed = hikari.Embed(colour=0x3B9DFF)
            embed.set_author(name=title, url=link)
            embed.set_image(img_url)

            await ctx.respond(embed)
        else:
            await ctx.respond(
                "Could not fetch a meme :c", flags=hikari.MessageFlag.EPHEMERAL
            )


"""
Animal picture + fact command
"""


@fun_group.child
@lightbulb.command("animal", "Get a fact + picture of an animal")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def animal_subcommand(ctx: lightbulb.Context) -> None:
    select_menu = (
        ctx.bot.rest.build_action_row()
        .add_select_menu("animal_select")
        .set_placeholder("Pick an animal")
    )

    for name, emoji in ANIMALS.items():
        select_menu.add_option(
            name,
            name.lower().replace(" ", "_"),
        ).set_emoji(emoji).add_to_menu()

    resp = await ctx.respond(
        "Pick an animal from the dropdown menu",
        component=select_menu.add_to_container(),
    )
    msg = await resp.message()

    try:
        event = await ctx.bot.wait_for(
            hikari.InteractionCreateEvent,
            timeout=60,
            predicate=lambda e: isinstance(e.interaction, hikari.ComponentInteraction)
            and e.interaction.user.id == ctx.author.id
            and e.interaction.message.id == msg.id
            and e.interaction.component_type == hikari.ComponentType.SELECT_MENU,
        )
    except asyncio.TimeoutError:
        await msg.edit("The menu timed out", components=[])
    else:
        animal = event.interaction.values[0]
        async with ctx.bot.d.aio_session.get(
            f"https://some-random-api.ml/animal/{animal}"
        ) as res:
            if res.ok:
                res = await res.json()
                embed = hikari.Embed(description=res["fact"], colour=0x3B9DFF)
                embed.set_image(res["image"])

                animal = animal.replace("_", " ")
                await msg.edit(
                    f"Here's a {animal} for you!", embed=embed, components=[]
                )
            else:
                await msg.edit(f"API returned a {res.status} status", components=[])


"""
Tic-Tac-Toe command
"""


class TicTacToeButtons(tungsten.Components):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button_group = self.create_button_group()
        self.turn = 0

    def set_players(self, player1: hikari.Member, player2: hikari.Member):
        self.player1 = player1
        self.player2 = player2

    def check_winner(self):
        button_rows = self.button_group.button_rows
        if (
            int(button_rows[0][0].state)
            == int(button_rows[0][1].state)
            == int(button_rows[0][2].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[1][0].state)
            == int(button_rows[1][1].state)
            == int(button_rows[1][2].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[2][0].state)
            == int(button_rows[2][1].state)
            == int(button_rows[2][2].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[0][0].state)
            == int(button_rows[1][0].state)
            == int(button_rows[2][0].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[0][1].state)
            == int(button_rows[1][1].state)
            == int(button_rows[2][1].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[0][2].state)
            == int(button_rows[1][2].state)
            == int(button_rows[2][2].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[0][0].state)
            == int(button_rows[1][1].state)
            == int(button_rows[2][2].state)
            != 0
        ):
            return True
        elif (
            int(button_rows[0][2].state)
            == int(button_rows[1][1].state)
            == int(button_rows[2][0].state)
            != 0
        ):
            return True
        else:
            return False

    def create_button_group(self):
        button_states = {
            0: tungsten.ButtonState(
                label="", style=hikari.ButtonStyle.SECONDARY, emoji="➖"
            ),
            1: tungsten.ButtonState(
                label="", style=hikari.ButtonStyle.PRIMARY, emoji="❌"
            ),
            2: tungsten.ButtonState(
                label="", style=hikari.ButtonStyle.SUCCESS, emoji="⭕"
            ),
        }
        button_rows = [
            [
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
            ],
            [
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
            ],
            [
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
                tungsten.Button(state=0, button_states=button_states),
            ],
        ]
        return tungsten.ButtonGroup(button_rows)

    async def button_callback(
        self,
        button: tungsten.Button,
        x: int,
        y: int,
        interaction: hikari.ComponentInteraction,
    ) -> None:

        if interaction.user.id == self.player1.id:
            currentPlayer = self.player1
            state_cycle = {0: 1, 1: 1, 2: 2}
        else:
            currentPlayer = self.player2
            state_cycle = {0: 2, 1: 1, 2: 2}

        self.button_group.edit_button(x, y, state=state_cycle[button.state])

        winnerPresent = self.check_winner()
        self.turn += 1

        if winnerPresent:
            self.disable_components()
            await self.edit_msg(
                f"{interaction.user.mention} has won the game!", components=self.build()
            )
        elif not winnerPresent and self.turn == 9:
            self.disable_components()
            await self.edit_msg(f"It's a Tie!", components=self.build())
        elif not winnerPresent and self.turn != 9:

            if currentPlayer.id == self.player1.id:
                await self.edit_msg(
                    f"{self.player2.mention}, it is your turn!", components=self.build()
                )
            else:
                await self.edit_msg(
                    f"{self.player1.mention}, it is your turn!", components=self.build()
                )


@fun_group.child
@lightbulb.option("player1", "Player 1", hikari.Member, required=True)
@lightbulb.option("player2", "Player 2", hikari.Member, required=True)
@lightbulb.command("ttt", "Play a game of tic tac toe")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def tictactoe_subcommand(ctx: lightbulb.Context) -> None:
    player1 = ctx.get_guild().get_member(ctx.options.player1)
    player2 = ctx.get_guild().get_member(ctx.options.player2)

    if not player1:
        await ctx.respond("Player 1 is not in the server.")
        return
    if not player2:
        await ctx.respond("Player 2 is not in the server.")
        return
    if player1.id == player2.id:
        await ctx.respond(f"{ctx.user.mention}, player 1 cannot be equal to player 2.")

    buttons = TicTacToeButtons(ctx)
    buttons.set_players(player1, player2)
    resp = await ctx.respond(
        f"{player1.mention}, it is your turn!", components=buttons.build()
    )
    await buttons.run(resp)


"""
Coinflip command
"""


@fun_group.child
@lightbulb.option("option1", "Option 1", str, required=True)
@lightbulb.option("option2", "Option 2", str, required=True)
@lightbulb.command("coinflip", "Flip a coin")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def coinflip_subcommand(ctx: lightbulb.Context) -> None:
    option1 = ctx.options.option1
    option2 = ctx.options.option2

    random.seed()
    choice = random.choice([0, 1])

    if choice == 0:
        await ctx.respond(f"**{option1}** has won the coin flip!")
    else:
        await ctx.respond(f"**{option2}** has won the coin flip!")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(fun_plugin)
