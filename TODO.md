# TODO

Implement HEAD method to hls endpoints.
TESTING_ENV_VAR in constants.py

# Refactor

With version 1.3.0, i'm scaling down this project to be a simple proxy for dispatcharr. The following changes will be made:

Remove all user management, the login screen, authentication. Get rid of user settings and user management pages. There will be no user.

Remove the web player.

Remove info pages, the purpose for this project is for use in dispatcharr

Remove all EPG code, this should now be handled by dispatcharr.

Only allow LAN IP access to everything, also IP allow list
