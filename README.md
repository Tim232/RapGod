# Rap God - Discord Edition

[Rap God](https://github.com/jedevc/royal-hackaway-2019) was a pretty cool hackathon project, built using the Nexmo API. I thought it would be cool to implement the same thing, but inside of Discord using voice channels...

## Usage

Invite the bot to your server or just DM it.
Use `!help` to get help in Discord.

##### In servers

- `!rap <word(s)> ` make a rap with the given words and play it in a voice channel
- `!lyrics <words(s)>` make a rap with the given words and just print it
- `!save` save the last rap played and upload it as an mp3

Server admin-only commands:
- `!voice_channel <name of voice channel>` set which voice channel raps should be played in
- `!lyrics_channel <name of text channel>` set which text channel the `!lyrics` command is allowed to be used allowed in (to reduce spam)

##### In a DM chat with the bot
- `!rap <word(s)> ` make a rap with the given words and upload it as an mp3
- `!lyrics <words(s)>` make a rap with the given words and just print it

## Setup Environment

Requires Python 3.6.7 or above.
```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
```

Requires command line application `ffmpeg` or `avconv` to load the backing tracks.

Then following python needs to be run to get the natural language data sets:
```python
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
```

## Configuration

##### Google Cloud Platform credentials

Follow [this guide](https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries#client-libraries-install-python) to get GCP text-to-speech working. Put the JSON file in the config folder and name it ```google_cloud_key.json```.

##### Discord credentials

Follow [this guide](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) to get a Discord bot setup on your server.

`config/discord.json`

```json
{
    "token": "<bot token goes here>",
    "thread_count":4,
    "command_prefix":"!"
}
```

`config/songs.json`

```json
{
  "artist name":"song name or * for all songs"
}
```

## Contributors

- [Will Russell](https://github.com/wrussell1999): Discord bot, text to speech with GCP, and mp3 layering.
- [Justin Chadwell](https://github.com/jedevc): Natural language processing and lyric generation.
- [Daniel Spencer](https://github.com/danielfspencer): Improving audio generation, adding features and making the bot scalable to multiple servers
