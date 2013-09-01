chcemvediet
===========

FOIA requests for the lazy



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
