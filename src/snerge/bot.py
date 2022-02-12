#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from typing import Optional

import asyncio
import random

from twitchio import Client, Channel, Chatter, Message  # type: ignore

from snerge import logging
from snerge.config import Config
from snerge.token import App
from prosegen import ProseGen


class Bot(Client):  # type: ignore
    config: Config
    quotes: ProseGen
    target: Optional[Channel]
    last_message: int
    _timer: Optional[asyncio.TimerHandle]
    _stop: bool = False

    def __init__(
        self,
        logger: logging.Logger,
        loop: asyncio.AbstractEventLoop,
        config: Config,
        app: App,
        quotes: ProseGen,
    ) -> None:

        super().__init__(
            token=app.irc_token,
            loop=loop,
            initial_channels=[config.channel],
        )

        self._timer = None
        self.target = None
        self.last_message = 0
        self.logger = logger
        self.config = config
        self.quotes = quotes

    async def _start(self) -> None:
        self.logger.info("Starting up IRC bot")

        await super().start()

    async def event_ready(self) -> None:
        self.logger.info("Connected as %s", self.nick)

        while not self.target:
            await self.join_channels([self.config.channel])
            self.target = self.get_channel(self.config.channel)

        await self.target.send("Never fear, Snerge is here!")
        self.loop.create_task(self.queue_quote())

    async def event_message(self, message: Message) -> None:
        # Ignore loop-back messages
        if not message.author or message.author.name.lower() == self.nick.lower():
            return

        # Note when chat last happened
        self.last_message = int(self.loop.time())
        self.logger.debug("Saw a message at %d", self.last_message)

        if not self.target:
            return

        # Commands can only be processed by mods, when we can reply.
        chatter = self.target.get_chatter(message.author.name)

        if not isinstance(chatter, Chatter) or not message.author.is_mod:
            return

        # !snerge command: send a quote!
        content = message.content.lower()
        if content == "!snerge" or content.startswith("!snerge "):
            self.logger.info("Manual Snerge by %s", message.author.name)
            await self.send_quote()

    async def queue_quote(self) -> None:
        if self._stop:
            return

        # If we haven't managed to connect to the channel, wait a while.
        if not self.target:
            next_call = random.randint(*self.config.startup_probe)
            self.logger.info("No target initialised, waiting %d seconds", next_call)

        # If we haven't heard from chat in a while, assume the stream is down
        elif self.loop.time() - self.last_message > self.config.chat_active_probe[0]:
            next_call = random.randint(*self.config.chat_active_probe)
            self.logger.debug("Chat not active, waiting %d seconds", next_call)

        # Otherwise, send off a quote
        else:
            self.loop.create_task(self.send_quote())
            next_call = random.randint(*self.config.auto_quote_time)

        # Queue the next attempt to send a quote
        self._timer = self.loop.call_later(
            next_call, lambda: self.loop.create_task(self.queue_quote())
        )

    async def send_quote(self) -> None:
        if not self.target:
            return

        quote = get_quote(self.quotes, *self.config.quote_length)

        self.logger.info("Sending quote %s", quote)

        # There is a 0.5% chance of Snerge going UwU!
        if random.randint(0, 200) == 0:
            await self.target.send("[UwU] " + owo_magic(quote) + " [UwU]")
        else:
            await self.target.send("sergeSnerge " + quote + " sergeSnerge")

    async def stop(self) -> None:
        self._stop = True

        if self._timer:
            self._timer.cancel()

        if self.target:
            await self.target.send("sergeSnerge Sleepy time!")

        await self.close()


def get_quote(quotes: ProseGen, min_length: int, max_length: int) -> str:
    # Max 100 attempts to generate a quote
    for _ in range(100):
        wisdom = quotes.make_statement(min_length)

        if min_length < len(wisdom) < max_length:
            return wisdom

    return "I don't like coffee."


def owo_magic(non_owo_string: str) -> str:
    """
    Converts a non_owo_string to an owo_string

    :param non_owo_string: normal string

    :return: owo_string
    """

    return (
        non_owo_string.replace("ove", "wuw")
        .replace("R", "W")
        .replace("r", "w")
        .replace("L", "W")
        .replace("l", "w")
    )


async def main() -> None:
    from snerge import config, token, quotes  # pylint: disable=import-outside-toplevel

    logging.init()
    logger = logging.get_logger()

    app = token.refresh_app_token()
    data = await quotes.load_data(logger, ProseGen(20))

    # Create the IRC bot
    bot = Bot(
        logger=logger,
        loop=asyncio.get_event_loop(),
        app=app,
        config=config.config(),
        quotes=data,
    )

    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
