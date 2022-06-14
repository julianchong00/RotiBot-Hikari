import asyncio

import hikari
import lightbulb

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


# WIP
@fun_group.child
@lightbulb.command("ttt", "Play a game of tic tac toe")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def tictactoe_subcommand(ctx: lightbulb.Context) -> None:
    button = hikari.ButtonComponent(
        type=2,
        style=hikari.ButtonStyle.SECONDARY,
        custom_id="button",
        label=None,
        emoji=None,
        url=None,
        is_disabled=False,
    )

    row = ctx.bot.rest.build_action_row().add_button(
        hikari.ButtonStyle.SECONDARY, button.custom_id
    )
    await ctx.respond("test", components=[row])


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(fun_plugin)
