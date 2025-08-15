# <p align=center> Discord Guild Members Scraper

All tht trash. Anyways I made changes so it doesnt fuckup all the time lol


### Features
- Ability to scrape the profile pictures of members in the following formats:
  - `webp`
  - `png`
  - `jpg`
  - `jpeg`
- Scrape all members Usernames, Discrimnators, IDs, Bios and PFPs to a `txt` file.
- Ability to specify which guilds to scrape in the JSON config file.
- Each guild has it's own folder so the data is easy to handle.



### Installation

- Clone repo from git
```sh
git clone https://github.com/IllNoobis/DiscordScraper.git
```

- Install the dependencies.
```sh
pip install -r requirements.txt
```
- Rename `config.json.example` to `config.json` and edit required settings.
  - Input `channel_id` if you wish to scrape members from a particular channel; else leave 0


### Usage
```sh
cd Discord-Scraper/source
python main.py 
```
