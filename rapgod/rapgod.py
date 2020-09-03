import io
import logging
import asyncio
import discord
from queue import Empty
from discord.ext import commands

from . import worker
from rapgod import config

VERSION = "v0.2.0"

config.load_config()
pool = worker.ContainedPool(thread_count=config.thread_count)
bot = commands.Bot(command_prefix=config.command_prefix)
# remove built-in help
bot.remove_command('help')
last_song_cache = {}


def main():
    logging.basicConfig(level=logging.INFO)
    print(f'Rap God {VERSION} starting...')
    pool.start()
    bot.run(config.token)
    pool.stop()


@bot.event
async def on_ready():
    bot.loop.create_task(response_dispatcher())
    print('Bot ready!')


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    text = (f'rap-god-discord {VERSION} usage:\n\n'
            '**!rap <word(s)>** - make a rap with the given words and play it '
            'in a voice channel\n'
            '**!lyrics <word(s)>** - make a rap with the given words and just'
            ' print it\n'
            '**!save** - save the last rap played and upload it as an mp3'
            )

    await ctx.send(text)


@bot.command()
async def lyrics(ctx):
    words = ctx.message.content.split(' ')

    if (len(words) < 2):
        await ctx.send('Invalid syntax.\nTry `!lyrics <words>`')
        return

    theme_words = ' '.join(words[1:])

    # in servers, we only respond to lyrics commands in the  designated lyrics
    # text channel to reduce spam
    if ctx.message.channel.type == discord.ChannelType.text:
        server_id_string = str(ctx.guild.id)
        try:
            lyrics_channel = config.lyrics_channel_map[server_id_string]
        except KeyError:
            await ctx.send('I can only print lyrics in a designated lyrics cha'
                           'nnel.\nA server admin should run the command `!lyr'
                           'ics_channel <name of text channel>` to set one.')
            return

        if lyrics_channel != ctx.message.channel.id:
            text_channel = bot.get_channel(lyrics_channel)
            await ctx.send('You can only use this command in the designated ly'
                           f'rics channel \'{text_channel.name}\'.')
            return

    print(f'- Enqueue \'gen_lyrics\' (theme \'{theme_words}\')')
    pool.enqueue('gen_lyrics', theme_words, ctx.message.channel.id)
    await ctx.trigger_typing()


@bot.command()
async def rap(ctx):
    words = ctx.message.content.split(' ')

    if (len(words) < 2):
        await ctx.send('Invalid syntax.\nTry `!rap <words>`')
        return

    theme_words = ' '.join(words[1:])

    if ctx.message.channel.type == discord.ChannelType.private:
        # For DM channels we just send the mp3 file because we can't call them
        print(f'- Enqueue \'make_mp3_track\' (theme \'{theme_words}\')')
        pool.enqueue('make_mp3_track', theme_words, ctx.message.channel.id)
    else:
        # For server channels we play PCM audio in the voice channel
        server_id_string = str(ctx.guild.id)
        try:
            voice_channel_id = config.voice_channel_map[server_id_string]
        except KeyError:
            await ctx.send('I don\'t know which voice channel to rap in.\n'
                           'A server admin should run the command `!voice_chan'
                           'nel <name of voice channel>` to fix this')
            return

        print(f'- Enqueue \'make_pcm_track\' (theme \'{theme_words}\')')
        pool.enqueue('make_pcm_track', theme_words, voice_channel_id)

    await ctx.trigger_typing()


@bot.command()
async def save(ctx):
    if ctx.message.channel.type != discord.ChannelType.text:
        # Last played songs only exist in servers, not DMs
        return

    server_id_string = str(ctx.guild.id)
    try:
        voice_channel_id = config.voice_channel_map[server_id_string]
        stream = last_song_cache[str(voice_channel_id)]

        print(f'- Enqueue \'pcm_to_mp3\'')
        pool.enqueue('pcm_to_mp3', stream, ctx.channel.id)
        await ctx.trigger_typing()
    except KeyError:
        await ctx.send('No previous song found')


@bot.command()
async def voice_channel(ctx):
    if ctx.message.channel.type != discord.ChannelType.text:
        return

    user_permissions = ctx.channel.permissions_for(ctx.message.author)

    if not user_permissions.administrator:
        await ctx.send('Only server admins can configure the voice channel')
        return

    words = ctx.message.content.split(' ')

    if len(words) != 2:
        await ctx.send('Usage: `!voice_channel <name of voice channel>`')
        return

    channel_name = words[1]

    channel_object = discord.utils.get(ctx.guild.voice_channels,
                                       name=channel_name)

    if channel_object is None:
        await ctx.send(f'No voice channel with name \'{channel_name}\' '
                       'found')
        return

    server_id_string = str(ctx.guild.id)
    config.voice_channel_map[server_id_string] = channel_object.id
    config.save_voice_channel_map()

    await ctx.send(f'Voice channel \'{channel_name}\' (id: '
                   f'{channel_object.id}) will be used')

    print(f'Server \'{server_id_string}\' associated voice channel is now '
          f'\'{channel_object.id}\'')


@bot.command()
async def lyrics_channel(ctx):
    if ctx.message.channel.type != discord.ChannelType.text:
        return

    user_permissions = ctx.channel.permissions_for(ctx.message.author)

    if not user_permissions.administrator:
        await ctx.send('Only server admins can configure the lyrics channel')
        return

    words = ctx.message.content.split(' ')

    if len(words) != 2:
        await ctx.send('Usage: `!lyrics_channel <name of a text channel>`')
        return

    channel_name = words[1]

    channel_object = discord.utils.get(ctx.guild.text_channels,
                                       name=channel_name)

    if channel_object is None:
        await ctx.send(f'No text channel with name \'{channel_name}\' '
                       'found')
        return

    server_id_string = str(ctx.guild.id)
    config.lyrics_channel_map[server_id_string] = channel_object.id
    config.save_lyrics_channel_map()

    await ctx.send(f'Text channel \'{channel_name}\' (id: '
                   f'{channel_object.id}) will be used for lyrics')

    print(f'Server \'{server_id_string}\' associated lyrics channel is now '
          f'\'{channel_object.id}\'')


async def response_dispatcher():
    while True:
        try:
            completed_task = pool.get_result()
            task_name, result, channel_id = completed_task

            if task_name == 'make_pcm_track':
                bot.loop.create_task(play_audio(result, channel_id))
            elif task_name == 'gen_lyrics':
                bot.loop.create_task(send_lyrics(result, channel_id))
            elif task_name in ['make_mp3_track', 'pcm_to_mp3']:
                bot.loop.create_task(upload_file(result, channel_id))
        except Empty:
            await asyncio.sleep(1)


async def send_lyrics(lyrics, channel_id):
    text_channel = bot.get_channel(channel_id)
    print(f'- Dispatch lryics to \'{text_channel}\'')
    # text messages can only be 2000 chars long
    await text_channel.send(lyrics[:2000])


async def upload_file(stream, channel_id):
    text_channel = bot.get_channel(channel_id)
    print(f'- Dispatch file to \'{text_channel}\'')

    file_object = discord.File(stream, filename='rap.mp3')
    await text_channel.send(file=file_object)


async def play_audio(stream, channel_id):
    voice_channel = bot.get_channel(channel_id)
    print(f'- Dispatch audio to \'{voice_channel}\'')

    last_song_cache[str(channel_id)] = io.BytesIO(stream.getvalue())

    try:
        voice_client = await voice_channel.connect()
    except discord.ClientException:
        print(f'Cannot connect to channel {voice_channel}')
        return

    if voice_client.is_playing():
        print(f'Channel {voice_channel} is busy')
        return
    else:
        buffer = discord.PCMAudio(stream)
        voice_client.play(buffer)

        # this loop can probably be removed by using the 'after=' kwarg
        # of play() that is called when it finishes. however, that seems
        # to be very hard to get to work with async functions
        while voice_client.is_playing():
            await asyncio.sleep(1)

        await voice_client.disconnect()
