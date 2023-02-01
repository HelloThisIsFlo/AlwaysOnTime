# Always On Time
> ### Python - Django - TDD - Oauth - Continuous Delivery
<br>

### ✨ Beautiful Automatic Timers 🔔  
#### Showing the time until your next event 📅, with live-updates 🔴
<br>
<br>


Main Screen              |  Settings Screen
:-------------------------:|:-------------------------:
![Main Screen](https://github.com/FlorianKempenich/AlwaysOnTime/raw/main/doc/main_screen.png)  |  ![Settings Screen](https://github.com/FlorianKempenich/AlwaysOnTime/raw/main/doc/settings_screen.png)

<br>
<br>

# Setup

1. Create DB directory
   - See below
2. `docker-compose run alwaysontime pipenv run python manage.py migrate`
3. `docker-compose run alwaysontime pipenv run python manage.py createsuperuser`
4. Setup All-Auth
   - See below

## Database

> Using SQLite 3

### Create DB Directory & symlink

```
sudo mkdir -p /var/lib/com.floriankempenich/alwaysontime/database
sudo chown -R floriankempenich:staff /var/lib/com.floriankempenich
ln -s /var/lib/com.floriankempenich/alwaysontime/database ./alwaysontime/database
```

> ### Explanation
> - DB Stored at `/var/lib/com.floriankempenich/alwaysontime/database/db.sqlite3`
> - App expects it at `./database/db.sqlite3`
>   - **Docker:** Mount as a volume => `$DB_DIR_HOST:/alwaysontime/database`
>     - `DB_DIR_HOST` is where the db can be found on the host
>       - Set locally in `.env` to `$HOME/.databases/alwaysontime`
>       - Set on pipeline in `.env` to `$HOME/.databases/alwaysontime`
>     - `alwaysontime` is the working directory in docker. It contains:
>       - Everything in the local `alwaysontime` folder
>       - `Pipfile` & `Pipfile.lock` from the root of the project
>   - **Locally:** Symlink (created above)

## All-Auth

1. Download credentials
   - https://console.cloud.google.com/apis/credentials?authuser=2&project=always-on-time-335408
1. In http://localhost:8100/admin/
   - In `Sites`
     - Make sure there is a Site
     - Get the `ID` of the Site
       - `1` if only element in table
   - In `Social Application`
     - Configure Google
       - `Provider`: `Google`   
         _**Important:** That name is used in the app and configured in the settings.
           Make sure to write exactly as it is_
       - `Name`: Whatever
       - `Client id`: Called `Client ID` by Google
       - `Secret key`: Called `Client secret` by Google
       - `Key`: Not needed, leave blank
       - Add `Site` to `Chosen sites`

> For more info: https://django-allauth.readthedocs.io/en/latest/providers.html#google
