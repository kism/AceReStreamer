# AceReStreamer Documentation

FastAPI based Ace Stream re-streamer.

<https://github.com/kism/AceReStreamer>

Repository readme: `/readme`

## Running and Configuration

Run the program, either by [docker-compose](deployment/docker.md) or [directly](deployment/non-docker.md).

When you run the program, a folder named `instance` will be created in the working directory. This folder will contain the `config.json` file, as well as cache and the SQLite database.

If there is no config.json file in the instance folder, the program will create one with the default values.

Environment vaiables will override the config values, and be saved to config.json. Have a look at `docker-compose.yml` for examples of environment variables.

### Reset password

`acerestreamer-password-reset` is an interactive cli tool to reset user passwords. If you are running in docker you can run it in the container, in the /app directory.

## Scraper Mode

`acerestreamer-scrape` is a tool that will scrape streams and provide them in m3u8 format for use with Horus and other Ace Stream clients.

## Development

```{toctree}
:maxdepth: 2
:caption: Develop

development/backend
development/frontend
development/docker
development/materials/xc_api
```
