# Minecraft but Sub=TP - RCON Server

## Install Required Module

```py
pip install -r requirements.txt
```

## Create a `.env` File

Copy the `.env.example` file and rename it to `.env`.

```sh
cp .env.example .env
```

## Get Your YouTube API Key

Log into the developer console at: https://console.developers.google.com/

Click "Enable APIs and Services" at the top of the screen.

Search for YouTube Data API v3 and enable it. If you have already enabled it click "Manage."

Under the credentials section, click "Create Credentials" on the right hand side of the screen.

Select "API Key" from the dropdown menu.

Copy the API key and paste it into the `.env` file.

## Get Your YouTube Channel ID

Log into YouTube and go to: https://www.youtube.com/account_advanced/

Copy the "Channel ID" and paste it into the `.env` file.

## Configure the MC Server

Open `server.properties` and edit the following lines:

```text
enable-rcon=true
rcon.password=password
rcon.port=25575
```

## Start the Rcon Server

```cli
python rcon.py
```
