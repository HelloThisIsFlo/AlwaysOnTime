# Setup All Auth


- In http://localhost:8100/admin/
  - In `Sites`
    - Make sure there is a Site
    - Get the `ID` of the Site
      - `1` if only element in table
  - In `Social Application`
    - Configure Google
      - `Provider`: “Google”
      - `Name`: Whatever
      - `Client id`: Called `Client ID` by Google
      - `Secret key`: Called `Client secret` by Google
      - `Key`: Not needed, leave blank
      - Add `Site` to `Chosen sites`

> For more info: https://django-allauth.readthedocs.io/en/latest/providers.html#google