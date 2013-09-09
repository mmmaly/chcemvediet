Chcem vediet
===========

PostgreSQL setup
----------------
Use the **/private/sql/create_db.sql** script on an empty database to create the database structure.
TODO: migration strategy, initial data stock

Environment variables
---------------------
These have to be configured in order for the app to work correctly.
* **PORT** - HTTP port that the app listens on (default: 8080)
* **DATABASE_URL** - PostgreSQL database connection URL
* **APP_URL** - The URL of the web site as deployed (e.g. https://www.chcemvediet.sk), used as a return URL for authentication services
* **TWITTER_KEY** - The consumer key used for twitter authentication (obtained by registering the app under developer.twitter.com)
* **TWITTER_SECRET** - The consumer secret used for twitter authentication (obtained by registering the app under developer.twitter.com)
* **FACEBOOK_APP_ID** - The app ID used for facebook authentication (obtained by registering the app under developer.facebook.com)
* **FACEBOOK_APP_SECRET** - The app secret used for facebook authentication (obtained by registering the app under developer.facebook.com)


Working with heroku
-------------------
* sign-up with Heroku
* install heroku-toorbelt https://toolbelt.heroku.com/
* heroku login
* heroku git:remote -a chcemvediet

From then on, just
* git push heroku 
to deploy to https://chcemvediet.herokuapp.com/

If you wish to receive notifications after every deployment,
* heroku addons:add deployhooks:email  --recipient=user@gmail.com --subject="chcemvediet Deployed" --body="{{user}} deployed {app}, see {url} for the new version. Details: {head} {head_long} {git_log}"
